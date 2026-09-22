class InstinctError(Exception):
    def __init__(self, message, line=None, col=None, filename=None):
        self.message  = message
        self.line     = line
        self.col      = col
        self.filename = filename
        super().__init__(self.format())

    def format(self):
        loc = ""
        if self.line is not None:
            loc = f" ({self.filename}:{self.line}:{self.col})"
        return f"{self.message}{loc}"


class LexError(InstinctError):
    pass