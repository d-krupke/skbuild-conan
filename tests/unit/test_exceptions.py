"""
Unit tests for custom exceptions.

These tests validate that custom exceptions have proper inheritance,
remediation messages, and formatting.
"""
import pytest
from skbuild_conan.exceptions import (
    SkbuildConanError,
    ConanVersionError,
    ConanProfileError,
    ConanDependencyError,
    ConanNetworkError,
    ConanRecipeError,
    ValidationError,
    VersionCompatibilityError,
    ConanOutputError,
)


class TestExceptionInheritance:
    """Test that all custom exceptions inherit correctly."""

    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from SkbuildConanError."""
        exceptions = [
            ConanVersionError("1.0", "2.x"),
            ConanProfileError("test_profile", "details"),
            ConanDependencyError("details"),
            ConanNetworkError("details"),
            ConanRecipeError("/path", "details"),
            ValidationError("details"),
            VersionCompatibilityError("details"),
            ConanOutputError("details"),
        ]

        for exc in exceptions:
            assert isinstance(exc, SkbuildConanError)
            assert isinstance(exc, Exception)


class TestConanVersionError:
    """Tests for ConanVersionError."""

    def test_includes_version_in_message(self):
        """Test that error message includes version numbers."""
        error = ConanVersionError("1.59.0", "2.x")
        message = str(error)
        assert "1.59.0" in message
        assert "2.x" in message

    def test_includes_remediation(self):
        """Test that error includes installation instructions."""
        error = ConanVersionError("1.59.0", "2.x")
        detailed = error.detailed_message()
        assert "pip install" in detailed.lower() or "conan" in detailed.lower()

    def test_detailed_message_formatting(self):
        """Test that detailed message is well-formatted."""
        error = ConanVersionError("1.59.0")
        detailed = error.detailed_message()
        assert "=" in detailed  # Has separators
        assert "ERROR" in detailed  # Has error header
        assert "https://github.com" in detailed  # Has help link


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_message(self):
        """Test that validation errors have clear messages."""
        error = ValidationError("Invalid requirement format")
        assert "Invalid requirement format" in str(error)

    def test_validation_error_remediation(self):
        """Test that validation errors suggest fixes."""
        error = ValidationError("test", remediation="Fix by doing X")
        detailed = error.detailed_message()
        assert "Fix by doing X" in detailed


class TestConanNetworkError:
    """Tests for ConanNetworkError."""

    def test_network_error_suggests_retry(self):
        """Test that network errors suggest retrying."""
        error = ConanNetworkError("Connection failed")
        detailed = error.detailed_message()
        # Should suggest it's transient and to try again
        lower_detailed = detailed.lower()
        assert "transient" in lower_detailed or "again" in lower_detailed or "retry" in lower_detailed


class TestConanRecipeError:
    """Tests for ConanRecipeError."""

    def test_recipe_error_includes_path(self):
        """Test that recipe errors include the problematic path."""
        error = ConanRecipeError("/path/to/recipe", "Missing conanfile.py")
        message = str(error)
        assert "/path/to/recipe" in message
        assert "Missing conanfile.py" in message

    def test_recipe_error_remediation(self):
        """Test that recipe errors provide guidance."""
        error = ConanRecipeError("/path/to/recipe", "Missing conanfile.py")
        detailed = error.detailed_message()
        # Should mention checking the recipe
        assert "recipe" in detailed.lower() or "conanfile" in detailed.lower()


class TestExceptionUsability:
    """Tests for exception usability."""

    def test_exception_can_be_raised(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(ConanVersionError) as exc_info:
            raise ConanVersionError("1.0", "2.x")

        assert "1.0" in str(exc_info.value)

    def test_exception_chain_preserved(self):
        """Test that exception chaining works."""
        original = ValueError("original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise ConanDependencyError("dependency failed") from e
        except ConanDependencyError as e:
            assert e.__cause__ is original

    def test_detailed_message_includes_separators(self):
        """Test that detailed messages are visually separated."""
        error = ValidationError("test error")
        detailed = error.detailed_message()

        # Should have visual separators
        assert "=" * 10 in detailed or "-" * 10 in detailed

    def test_detailed_message_includes_help_link(self):
        """Test that all detailed messages link to GitHub issues."""
        errors = [
            ConanVersionError("1.0"),
            ValidationError("test"),
            ConanNetworkError("test"),
        ]

        for error in errors:
            detailed = error.detailed_message()
            assert "github.com/d-krupke/skbuild-conan" in detailed
