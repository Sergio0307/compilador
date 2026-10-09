"""Fase 3: análisis semántico (validaciones de compilación, spec 2.8).

Recibe un SpeciesDef ya parseado y lo valida contra la spec. A diferencia
del lexer y el parser, que paran en el primer fallo, aquí recorremos todo
el AST y acumulamos TODOS los errores en una lista, para reportarlos juntos.
"""

from lang.errors import SemanticError
from lang.catalog import HEADER_KEYS, CONSTANTS, READONLY
from lang.ast_nodes import Assign


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

        Punto 2: cabecera. Los puntos 3 (goto a etiquetas existentes) y 4
        (asignación a percepción/constante) añaden aquí sus comprobaciones.
        """
        self.errors = []
        self._check_header(species)
        self._check_jumps(species)
        self._check_assignments(species)
        return self.errors


    # Punto 2: cabecera (spec 2.2)


    @staticmethod
    def _is_number(value):
        """¿El valor crudo de cabecera era un literal numérico?
        El lexer separa números de nombres, así que un nombre nunca es
        todo dígitos (con '-' opcional delante)."""
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _check_header(self, species):
        """Valida las cinco claves obligatorias, duplicadas, desconocidas,
        tipo (nombre/número) y rango. Acumula todos los fallos."""
        vistos = {}   # clave -> (valor, línea)
        for key, value, line in species.header:
            if key not in HEADER_KEYS:
                self.error(f"clave de cabecera desconocida '{key}'", line=line)
                continue
            if key in vistos:
                self.error(f"clave de cabecera duplicada '{key}'", line=line)
                continue
            vistos[key] = (value, line)

        # Faltantes: rechazo (decisión A). Sin línea propia, se reportan
        # en la línea de 'creature' (primera línea de la cabecera).
        for key in HEADER_KEYS:
            if key not in vistos:
                self.error(f"falta la clave obligatoria '{key}'", line=species.line)

        # Tipo y rango de cada clave presente
        for key, (value, line) in vistos.items():
            spec = HEADER_KEYS[key]
            if spec["kind"] == "name":
                if self._is_number(value):
                    self.error(f"'{key}' debe ser un nombre, no un número", line=line)
            else:   # "int"
                if not self._is_number(value):
                    self.error(f"'{key}' debe ser un número entero", line=line)
                elif int(value) < spec["min"]:
                    self.error(
                        f"'{key}' debe ser >= {spec['min']} (se encontró {value})",
                        line=line,
                    )


    # Punto 3: saltos a etiquetas existentes (spec 2.3 y 2.8)


    def _check_jumps(self, species):
        """Valida que cada goto / if...goto apunte a una etiqueta existente.

        Los nodos de salto (Goto, IfGoto) son los unicos con atributo
        `label`; Label usa `name`. Por eso basta un getattr, sin ramas por
        tipo de nodo.
        """
        labels = set(species.blocks)
        for block in species.blocks.values():
            for instr in block.instructions:
                destino = getattr(instr, "label", None)
                if destino is not None and destino not in labels:
                    self.error(
                        f"en el bloque '{block.label}': goto a etiqueta "
                        f"inexistente '{destino}'",
                        line=instr.line,
                    )


    # Punto 4: no se puede asignar a una percepción ni a una constante (spec 2.3)


    def _check_assignments(self, species):
        """Rechaza asignaciones cuyo destino sea de solo lectura (READONLY).

        Solo acepta asignar a variables propias: crear una variable nueva
        (que no existía) está permitido; lo prohibido es pisar una
        percepción o una constante.
        """
        for block in species.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, Assign) and instr.name in READONLY:
                    tipo = "constante" if instr.name in CONSTANTS else "percepción"
                    self.error(
                        f"no se puede asignar a la {tipo} '{instr.name}'",
                        line=instr.line,
                    )
