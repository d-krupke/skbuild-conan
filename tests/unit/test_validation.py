"""
Unit tests for input validation.

These tests validate that setup arguments are properly validated
before expensive conan operations are performed.
"""
import os
import pytest
from pathlib import Path
from skbuild_conan.setup_wrapper import validate_setup_args
from skbuild_conan.exceptions import ValidationError


class TestRequirementValidation:
    """Tests for conan_requirements validation."""

    def test_valid_requirement_accepted(self):
        """Test that valid requirements are accepted."""
        # Should not raise
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=["fmt/10.0.0"]
        )

    def test_requirement_with_version_range_accepted(self):
        """Test that version ranges are accepted."""
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=["fmt/[>=10.0.0]"]
        )

    def test_requirement_without_slash_rejected(self):
        """Test that requirements without '/' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile=".",
                conan_recipes=None,
                conan_requirements=["invalid_format"]
            )

        assert "Invalid requirement format" in str(exc_info.value)
        assert "invalid_format" in str(exc_info.value)

    def test_multiple_invalid_requirements_all_reported(self):
        """Test that all invalid requirements are reported."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile=".",
                conan_recipes=None,
                conan_requirements=["invalid1", "fmt/10.0.0", "invalid2"]
            )

        error_msg = str(exc_info.value)
        assert "invalid1" in error_msg
        assert "invalid2" in error_msg
        # Valid one should not be in error
        assert "fmt/10.0.0" not in error_msg

    def test_empty_requirements_accepted(self):
        """Test that no requirements is valid."""
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=None
        )


class TestConanfileValidation:
    """Tests for conanfile path validation."""

    def test_default_conanfile_path_accepted(self):
        """Test that default '.' path is accepted."""
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=None
        )

    def test_nonexistent_conanfile_rejected(self):
        """Test that non-existent conanfile path is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile="/nonexistent/path",
                conan_recipes=None,
                conan_requirements=None
            )

        assert "does not exist" in str(exc_info.value)
        assert "/nonexistent/path" in str(exc_info.value)

    def test_existing_conanfile_accepted(self, tmp_path):
        """Test that existing conanfile path is accepted."""
        # Create a temporary directory
        test_dir = tmp_path / "conan_test"
        test_dir.mkdir()

        validate_setup_args(
            conanfile=str(test_dir),
            conan_recipes=None,
            conan_requirements=None
        )


class TestRecipeValidation:
    """Tests for conan_recipes validation."""

    def test_nonexistent_recipe_path_rejected(self):
        """Test that non-existent recipe paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile=".",
                conan_recipes=["/nonexistent/recipe"],
                conan_requirements=None
            )

        error_msg = str(exc_info.value)
        assert "Recipe path does not exist" in error_msg
        assert "/nonexistent/recipe" in error_msg

    def test_recipe_without_conanfile_rejected(self, tmp_path):
        """Test that recipe directory without conanfile.py is rejected."""
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()

        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile=".",
                conan_recipes=[str(recipe_dir)],
                conan_requirements=None
            )

        error_msg = str(exc_info.value)
        assert "Missing conanfile.py" in error_msg
        assert str(recipe_dir) in error_msg

    def test_valid_recipe_accepted(self, tmp_path):
        """Test that valid recipe directory is accepted."""
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        # Should not raise
        validate_setup_args(
            conanfile=".",
            conan_recipes=[str(recipe_dir)],
            conan_requirements=None
        )

    def test_multiple_recipes_validated(self, tmp_path):
        """Test that all recipes are validated."""
        # Create one valid and one invalid recipe
        valid_recipe = tmp_path / "valid"
        valid_recipe.mkdir()
        (valid_recipe / "conanfile.py").touch()

        invalid_recipe = tmp_path / "invalid"
        invalid_recipe.mkdir()
        # No conanfile.py

        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile=".",
                conan_recipes=[str(valid_recipe), str(invalid_recipe)],
                conan_requirements=None
            )

        # Should report the invalid one
        assert "invalid" in str(exc_info.value)


class TestMutuallyExclusiveOptions:
    """Tests for mutually exclusive option validation."""

    def test_both_conanfile_and_requirements_rejected(self):
        """Test that conanfile and requirements cannot both be specified."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile="/custom/path",
                conan_recipes=None,
                conan_requirements=["fmt/10.0.0"]
            )

        error_msg = str(exc_info.value)
        assert "Cannot specify both" in error_msg
        assert "conanfile" in error_msg.lower()
        assert "requirements" in error_msg.lower()

    def test_default_conanfile_with_requirements_accepted(self):
        """Test that default conanfile (.) with requirements is accepted."""
        # This is the common case - should work
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=["fmt/10.0.0"]
        )


class TestErrorMessageQuality:
    """Tests for error message quality and usability."""

    def test_error_message_is_multiline_for_multiple_errors(self):
        """Test that multiple errors are reported on separate lines."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile="/nonexistent",
                conan_recipes=["/fake/recipe"],
                conan_requirements=["invalid"]
            )

        error_msg = str(exc_info.value)
        # Should have multiple lines
        lines = error_msg.split("\n")
        assert len(lines) > 1

    def test_error_message_mentions_all_problems(self):
        """Test that all problems are mentioned in error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_setup_args(
                conanfile="/nonexistent",
                conan_recipes=["/fake/recipe"],
                conan_requirements=["invalid"]
            )

        error_msg = str(exc_info.value)
        # All three problems should be mentioned
        assert "nonexistent" in error_msg  # conanfile issue
        assert "fake/recipe" in error_msg or "does not exist" in error_msg  # recipe issue
        assert "invalid" in error_msg  # requirement issue
