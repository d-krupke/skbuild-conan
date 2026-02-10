"""
Logging utilities for skbuild-conan.

Provides structured logging with configurable verbosity levels and
cross-platform color support for better transparency.
"""
import os
import sys
import time
from enum import IntEnum
from typing import Optional

# Try to import colorama for cross-platform color support
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback color codes (will work on Unix-like systems)
    class Fore:
        BLUE = '\033[94m' if sys.platform != 'win32' else ''
        RED = '\033[91m' if sys.platform != 'win32' else ''
        YELLOW = '\033[93m' if sys.platform != 'win32' else ''
        GREEN = '\033[92m' if sys.platform != 'win32' else ''
        CYAN = '\033[96m' if sys.platform != 'win32' else ''

    class Style:
        RESET_ALL = '\033[0m' if sys.platform != 'win32' else ''


class LogLevel(IntEnum):
    """Log verbosity levels."""
    QUIET = 0    # Only errors
    NORMAL = 1   # Standard operation messages
    VERBOSE = 2  # Detailed operation info
    DEBUG = 3    # Everything including conan output


class Logger:
    """
    Structured logger for skbuild-conan operations.

    Provides different log levels for better transparency and debugging.
    Supports colored output on all platforms when colorama is available.
    """

    def __init__(self, log_level: Optional[LogLevel] = None):
        """
        Initialize the logger.

        Args:
            log_level: The logging level. If None, reads from environment
                      variable SKBUILD_CONAN_LOG_LEVEL (quiet/normal/verbose/debug).
                      Defaults to NORMAL.
        """
        if log_level is None:
            log_level = self._get_log_level_from_env()
        self.log_level = log_level
        self._phase_start_time: Optional[float] = None
        self._current_phase: Optional[str] = None

    def _get_log_level_from_env(self) -> LogLevel:
        """Get log level from environment variable."""
        env_level = os.environ.get('SKBUILD_CONAN_LOG_LEVEL', 'normal').lower()
        level_map = {
            'quiet': LogLevel.QUIET,
            'normal': LogLevel.NORMAL,
            'verbose': LogLevel.VERBOSE,
            'debug': LogLevel.DEBUG,
        }
        return level_map.get(env_level, LogLevel.NORMAL)

    def error(self, msg: str):
        """Log an error message (always shown)."""
        print(f"{Fore.RED}[skbuild-conan ERROR] {msg}{Style.RESET_ALL}", file=sys.stderr)

    def warning(self, msg: str):
        """Log a warning message (shown at NORMAL and above)."""
        if self.log_level >= LogLevel.NORMAL:
            print(f"{Fore.YELLOW}[skbuild-conan WARN] {msg}{Style.RESET_ALL}", file=sys.stderr)

    def info(self, msg: str):
        """Log an info message (shown at NORMAL and above)."""
        if self.log_level >= LogLevel.NORMAL:
            print(f"[skbuild-conan] {msg}")

    def success(self, msg: str):
        """Log a success message (shown at NORMAL and above)."""
        if self.log_level >= LogLevel.NORMAL:
            print(f"{Fore.GREEN}[skbuild-conan] {msg}{Style.RESET_ALL}")

    def verbose(self, msg: str):
        """Log a verbose message (shown at VERBOSE and above)."""
        if self.log_level >= LogLevel.VERBOSE:
            print(f"{Fore.CYAN}[skbuild-conan] {msg}{Style.RESET_ALL}")

    def debug(self, msg: str, exc_info: bool = False):
        """Log a debug message (shown at DEBUG only).

        Args:
            msg: The message to log
            exc_info: If True, add exception information (for compatibility with logging)
        """
        if self.log_level >= LogLevel.DEBUG:
            print(f"[skbuild-conan DEBUG] {msg}")
            if exc_info:
                import traceback
                traceback.print_exc()

    def command(self, cmd: str):
        """Log a command being executed (shown at NORMAL and above)."""
        if self.log_level >= LogLevel.NORMAL:
            print(f"{Fore.BLUE}[skbuild-conan] $ {cmd}{Style.RESET_ALL}")

    def enter_phase(self, phase_name: str):
        """
        Enter a build phase and log it.

        Args:
            phase_name: Name of the phase being entered
        """
        self._current_phase = phase_name
        self._phase_start_time = time.time()
        if self.log_level >= LogLevel.NORMAL:
            print(f"\n{'='*60}")
            print(f"[skbuild-conan] {phase_name}")
            print(f"{'='*60}")

    def exit_phase(self, success: bool = True):
        """
        Exit a build phase and log the duration.

        Args:
            success: Whether the phase completed successfully
        """
        if self._phase_start_time is not None:
            elapsed = time.time() - self._phase_start_time
            if self.log_level >= LogLevel.VERBOSE:
                status = f"{Fore.GREEN}completed{Style.RESET_ALL}" if success else f"{Fore.RED}failed{Style.RESET_ALL}"
                print(f"[skbuild-conan] Phase {status} in {elapsed:.1f}s")

        self._current_phase = None
        self._phase_start_time = None

    def conan_output(self, output: str):
        """
        Log conan command output.

        Args:
            output: The output from conan command
        """
        if self.log_level >= LogLevel.DEBUG:
            # In debug mode, show full output
            for line in output.splitlines():
                print(f"  {line}")
        elif self.log_level >= LogLevel.VERBOSE:
            # In verbose mode, show full output when small, summary when large
            lines = output.splitlines()
            if len(lines) <= 10:
                for line in lines:
                    print(f"  {line}")
            else:
                for line in lines[:5]:
                    print(f"  {line}")
                print(f"  ... ({len(lines) - 5} more lines)")
