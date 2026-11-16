class InstinctError(Exception):
    def __init__(self, message, line=None, col=None, filename=None, code=None):
        self.message  = message
        self.line     = line
        self.col      = col
        self.filename = filename
        self.code     = code  # NUEVO: código de error (ej. "E_LEX_001")
        super().__init__(self.format())

    def format(self):
        loc = ""
        if self.line is not None:
            loc = f" ({self.filename}:{self.line}"
            if self.col is not None:
                loc += f":{self.col}"
            loc += ")"
        code_str = f" [{self.code}]" if self.code else ""
        return f"{self.message}{code_str}{loc}"


class LexError(InstinctError):
    """Error léxico: carácter inesperado, número inválido, string sin cerrar, etc."""
    pass


class ParseError(InstinctError):
    """Error sintáctico: estructura inválida, token inesperado, etc."""
    pass


class SemanticError(InstinctError):
    """Error semántico: clave faltante, goto inválido, asignación prohibida, etc."""
    pass


class RuntimeFault(InstinctError):
    """Error en tiempo de ejecución (spec 2.8): el bicho muere de un ictus.

    Se llama RuntimeFault y no RuntimeError para no pisar el builtin. Lo
    lanza el intérprete (expresiones y acciones); el simulador lo captura,
    mata a la criatura y escribe el mensaje en los logs.
    """
    pass


class SemanticErrors(InstinctError):
    """Varios SemanticError agrupados para reportarlos todos juntos.

    La fase semántica recorre el AST completo aunque encuentre fallos, así
    que acumula la lista y la lanza de una sola vez (Fase 3).
    """

    def __init__(self, errors):
        self.errors = list(errors)
        # code genérico para grupo
        super().__init__("errores semánticos", code="E_SEM_MULTIPLE")

    def format(self):
        code_str = f" [{self.code}]" if self.code else ""
        return f"errores semánticos{code_str}:\n  " + "\n  ".join(
            e.format() for e in self.errors
        )