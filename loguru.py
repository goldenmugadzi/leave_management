"""
Minimal shim for the `loguru` logger used in parts of the project during tests.
Prevents ImportError when the real `loguru` package is not installed.
"""

class _Logger:
    def info(self, *args, **kwargs):
        pass

    def success(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


logger = _Logger()
