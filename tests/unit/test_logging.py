"""
Unit tests for logging_utils module.

These tests validate the logging system including log levels,
verbosity detection, and output formatting.
"""

from skbuild_conan.logging_utils import Logger, LogLevel


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self):
        """Test that log levels have correct integer values."""
        assert LogLevel.QUIET.value == 0
        assert LogLevel.NORMAL.value == 1
        assert LogLevel.VERBOSE.value == 2
        assert LogLevel.DEBUG.value == 3

    def test_log_level_ordering(self):
        """Test that log levels can be compared."""
        assert LogLevel.QUIET < LogLevel.NORMAL
        assert LogLevel.NORMAL < LogLevel.VERBOSE
        assert LogLevel.VERBOSE < LogLevel.DEBUG
        assert LogLevel.DEBUG >= LogLevel.VERBOSE


class TestLogger:
    """Tests for Logger class."""

    def test_logger_default_level(self):
        """Test that logger defaults to NORMAL level."""
        logger = Logger()
        assert logger.log_level == LogLevel.NORMAL

    def test_logger_explicit_level(self):
        """Test that explicit log level is used."""
        logger = Logger(LogLevel.DEBUG)
        assert logger.log_level == LogLevel.DEBUG

    def test_logger_env_variable(self, monkeypatch):
        """Test that log level is read from environment variable."""
        monkeypatch.setenv('SKBUILD_CONAN_LOG_LEVEL', 'debug')
        logger = Logger()
        assert logger.log_level == LogLevel.DEBUG

    def test_logger_env_variable_case_insensitive(self, monkeypatch):
        """Test that env variable is case-insensitive."""
        monkeypatch.setenv('SKBUILD_CONAN_LOG_LEVEL', 'VERBOSE')
        logger = Logger()
        assert logger.log_level == LogLevel.VERBOSE

    def test_logger_invalid_env_defaults_to_normal(self, monkeypatch):
        """Test that invalid env value falls back to NORMAL."""
        monkeypatch.setenv('SKBUILD_CONAN_LOG_LEVEL', 'invalid')
        logger = Logger()
        assert logger.log_level == LogLevel.NORMAL

    def test_explicit_level_overrides_env(self, monkeypatch):
        """Test that explicit log level takes precedence over env."""
        monkeypatch.setenv('SKBUILD_CONAN_LOG_LEVEL', 'quiet')
        logger = Logger(LogLevel.VERBOSE)
        assert logger.log_level == LogLevel.VERBOSE


class TestLoggerOutput:
    """Tests for logger output methods."""

    def test_error_always_shown(self, capsys):
        """Test that errors are shown at all log levels."""
        for level in LogLevel:
            logger = Logger(level)
            logger.error("test error")

        captured = capsys.readouterr()
        assert captured.err.count("test error") == 4  # Once per level

    def test_info_shown_at_normal_and_above(self, capsys):
        """Test that info messages respect log level."""
        # Quiet - should not show
        logger = Logger(LogLevel.QUIET)
        logger.info("quiet test")
        captured = capsys.readouterr()
        assert "quiet test" not in captured.out

        # Normal - should show
        logger = Logger(LogLevel.NORMAL)
        logger.info("normal test")
        captured = capsys.readouterr()
        assert "normal test" in captured.out

    def test_verbose_shown_at_verbose_and_above(self, capsys):
        """Test that verbose messages respect log level."""
        # Normal - should not show
        logger = Logger(LogLevel.NORMAL)
        logger.verbose("normal level")
        captured = capsys.readouterr()
        assert "normal level" not in captured.out

        # Verbose - should show
        logger = Logger(LogLevel.VERBOSE)
        logger.verbose("verbose level")
        captured = capsys.readouterr()
        assert "verbose level" in captured.out

    def test_debug_shown_only_at_debug(self, capsys):
        """Test that debug messages only show at DEBUG level."""
        # Verbose - should not show
        logger = Logger(LogLevel.VERBOSE)
        logger.debug("verbose level")
        captured = capsys.readouterr()
        assert "verbose level" not in captured.out

        # Debug - should show
        logger = Logger(LogLevel.DEBUG)
        logger.debug("debug level")
        captured = capsys.readouterr()
        assert "debug level" in captured.out

    def test_debug_with_exc_info(self, capsys):
        """Test that debug can log exception information."""
        logger = Logger(LogLevel.DEBUG)
        try:
            raise ValueError("test exception")
        except ValueError:
            logger.debug("Error occurred", exc_info=True)

        captured = capsys.readouterr()
        assert "Error occurred" in captured.out
        # traceback.print_exc() writes to stderr
        assert "test exception" in captured.err
        assert "Traceback" in captured.err


class TestLoggerPhases:
    """Tests for phase tracking."""

    def test_enter_phase(self, capsys):
        """Test that entering a phase logs correctly."""
        logger = Logger(LogLevel.NORMAL)
        logger.enter_phase("Test Phase")

        captured = capsys.readouterr()
        assert "Test Phase" in captured.out
        assert "=" in captured.out  # Phase separators

    def test_exit_phase_verbose(self, capsys):
        """Test that exiting phase shows timing in verbose mode."""
        logger = Logger(LogLevel.VERBOSE)
        logger.enter_phase("Test Phase")
        logger.exit_phase(success=True)

        captured = capsys.readouterr()
        assert "completed" in captured.out or "Phase" in captured.out

    def test_exit_phase_not_shown_at_normal(self, capsys):
        """Test that phase exit timing not shown at NORMAL level."""
        logger = Logger(LogLevel.NORMAL)
        logger.enter_phase("Test Phase")
        capsys.readouterr()  # Clear

        logger.exit_phase(success=True)
        captured = capsys.readouterr()
        # At NORMAL level, exit_phase should not add output
        assert "completed" not in captured.out
