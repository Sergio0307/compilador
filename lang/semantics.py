"""Fase 3: análisis semántico (validaciones de compilación, spec 2.8).

Recibe un SpeciesDef ya parseado y lo valida contra la spec. A diferencia
del lexer y el parser, que paran en el primer fallo, aquí recorremos todo
el AST y acumulamos TODOS los errores en una lista, para reportarlos juntos.
"""

from lang.errors import SemanticError


class SemanticAnalyzer:
    def __init__(self, filename="<input>"):
        self.filename = filename
        self.errors = []

    def error(self, message, line=None):
        """Registra un error semántico y sigue analizando."""
        self.errors.append(
            SemanticError(message, line=line, filename=self.filename)
        )

    def analyze(self, species):
        """Valida `species` y devuelve la lista de errores (vacía si todo bien).

        Los puntos 2 (cabecera), 3 (goto a etiquetas existentes) y 4
        (asignación a percepción/constante) añaden aquí sus comprobaciones,
        apoyándose en el catálogo de lang/catalog.py.
        """
        self.errors = []
        return self.errors
