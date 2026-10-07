from dataclasses import dataclass

@dataclass
class SpeciesDef:
    """Toda la definición de una especie (un archivo .ins)."""
    name: str                   # "Uruk" (vacío si faltó la clave; fase 3)
    faction: str                # "isengard" (vacío si faltó la clave; fase 3)
    health: int                 # 80 (0 si faltó o no es número; fase 3)
    vision: int                 # 6  (ídem)
    lifespan: int               # 400 (ídem)
    blocks: dict                # {"start": Block, "wander": Block, ...}
    header: list                # [(clave, valor, línea), ...] crudo: lo valida la fase 3
    line: int = 0               # línea donde aparece 'creature'


@dataclass
class Block:
    """Un bloque de comportamiento, encabezado por una etiqueta."""
    label: str                  # "start", "wander", "bite", ...
    instructions: list          # [IfGoto, Goto, Call, ...]



# Instrucciones


@dataclass
class Label:
    """name: — marca un punto al que se puede saltar. No consume turno."""
    name: str                   # "wander", "bite", "start", ...
    line: int = 0               # línea donde aparece la etiqueta


@dataclass
class IfGoto:
    """if COND goto LABEL"""
    condition: object           # nodo de expresión
    label: str                  # "flee"
    line: int = 0


@dataclass
class Goto:
    """goto LABEL"""
    label: str                  # "start"
    line: int = 0


@dataclass
class Call:
    """move(...), say(...), consume(...), etc."""
    name: str                   # "move", "say", "consume", ...
    args: list                  # [expr, expr, ...]
    line: int = 0


@dataclass
class Assign:
    """name = expr"""
    name: str                   # "home_x"
    expr: object                # nodo de expresión
    line: int = 0               # línea del '='



# Expresiones


@dataclass
class Number:
    """80, 6, 400, 15..."""
    value: int
    line: int = 0               # línea donde aparece el literal


@dataclass
class String:
    """"meat is back on the menu" (sin las comillas)"""
    value: str
    line: int = 0               # línea donde aparece el literal


@dataclass
class Identifier:
    """health, enemy_dist, GROUND, random, start..."""
    name: str
    line: int = 0               # línea donde aparece el identificador


@dataclass
class BinaryOp:
    """a + b, a < b, a and b, etc."""
    op: str                     # "+", "-", "<", "==", "and", "or", ...
    left: object                # nodo de expresión
    right: object               # nodo de expresión
    line: int = 0               # línea del operador


@dataclass
class UnaryOp:
    """-a, not a"""
    op: str                     # "-", "not"
    operand: object             # nodo de expresión
    line: int = 0               # línea del operador


