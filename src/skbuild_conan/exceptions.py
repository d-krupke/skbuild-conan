"""
Custom exceptions for skbuild-conan.

Provides context-aware error messages with remediation suggestions.
"""
from typing import Optional


class SkbuildConanError(Exception):
    """Base exception for all skbuild-conan errors."""

    def __init__(self, message: str, remediation: Optional[str] = None):
        """
        Initialize the exception.

        Args:
            message: The error message
            remediation: Optional suggestion for fixing the issue
        """
        self.remediation = remediation
        super().__init__(message)

    def detailed_message(self) -> str:
        """Get a detailed error message with remediation if available."""
        msg = [f"\n{'='*60}"]
        msg.append(f"ERROR: {str(self)}")
        msg.append(f"{'='*60}")

        if self.remediation:
            msg.append(f"\nSuggested fix:\n{self.remediation}")

        msg.append(f"\nFor more help: https://github.com/d-krupke/skbuild-conan/issues")
        msg.append(f"{'='*60}\n")
        return '\n'.join(msg)


class ConanVersionError(SkbuildConanError):
    """Raised when conan version is incompatible."""

    def __init__(self, current_version: str, required_version: str = "2.x"):
        super().__init__(
            f"Conan {current_version} is not compatible. Required: {required_version}",
            remediation="Install Conan 2.x: pip install 'conan>=2.0.0'"
        )


class ConanProfileError(SkbuildConanError):
    """Raised when there's an issue with the conan profile."""

    def __init__(self, profile_name: str, details: str = ""):
        super().__init__(
            f"Conan profile '{profile_name}' error: {details}",
            remediation=f"Check or delete the profile: ~/.conan2/profiles/{profile_name}\n"
                       f"It will be automatically recreated on next run."
        )


class ConanDependencyError(SkbuildConanError):
    """Raised when dependency resolution fails."""

    def __init__(self, details: str):
        super().__init__(
            f"Failed to resolve dependencies: {details}",
            remediation="Check that:\n"
                       "1. Dependency names and versions are correct\n"
                       "2. Required packages exist in ConanCenter or your remotes\n"
                       "3. Your conan profile is configured correctly\n"
                       "4. You have internet connection"
        )


class ConanNetworkError(SkbuildConanError):
    """Raised when network operations fail."""

    def __init__(self, details: str):
        super().__init__(
            f"Network error during conan operation: {details}",
            remediation="This is often a transient issue. Try:\n"
                       "1. Running the command again\n"
                       "2. Checking your internet connection\n"
                       "3. Verifying you can access conan remotes"
        )


class ConanRecipeError(SkbuildConanError):
    """Raised when there's an issue with a conan recipe."""

    def __init__(self, recipe_path: str, details: str):
        super().__init__(
            f"Error with recipe at '{recipe_path}': {details}",
            remediation="Check that:\n"
                       "1. The recipe path is correct\n"
                       "2. The recipe contains a valid conanfile.py\n"
                       "3. The recipe can be built successfully"
        )


class ValidationError(SkbuildConanError):
    """Raised when input validation fails."""

    def __init__(self, details: str):
        super().__init__(
            f"Invalid configuration: {details}",
            remediation="Review your setup() call parameters and fix the issues listed above."
        )


class VersionCompatibilityError(SkbuildConanError):
    """Raised when version compatibility check fails."""

    def __init__(self, details: str):
        super().__init__(
            f"Version compatibility issue: {details}",
            remediation="Update the incompatible packages to supported versions."
        )


class ConanOutputError(SkbuildConanError):
    """Raised when conan output cannot be parsed."""

    def __init__(self, details: str):
        super().__init__(
            f"Failed to parse conan output: {details}",
            remediation="This is likely a bug in skbuild-conan or an incompatible conan version.\n"
                       "Please report this issue."
        )
