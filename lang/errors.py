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
            loc = f" ({self.filename}:{self.line}"
            if self.col is not None:
                loc += f":{self.col}"
            loc += ")"
        return f"{self.message}{loc}"


class LexError(InstinctError):
    pass


class ParseError(InstinctError):
    pass


class SemanticError(InstinctError):
    pass


class SemanticErrors(InstinctError):
    """Varios SemanticError agrupados para reportarlos todos juntos.

    La fase semántica recorre el AST completo aunque encuentre fallos, así
    que acumula la lista y la lanza de una sola vez (Fase 3).
    """

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__(self.format())

    def format(self):
        return "errores semánticos:\n  " + "\n  ".join(
            e.format() for e in self.errors
        )