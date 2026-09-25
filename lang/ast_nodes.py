from dataclasses import dataclass

@dataclass
class SpeciesDef:
    """Toda la definición de una especie (un archivo .ins)."""
    name: str                   # "Uruk"
    faction: str                # "isengard"
    health: int                 # 80
    vision: int                 # 6
    lifespan: int               # 400
    blocks: dict                # {"start": Block, "wander": Block, ...}
    line: int = 0               # línea donde aparece 'creature'


@dataclass
class Block:
    """Un bloque de comportamiento, encabezado por una etiqueta."""
    label: str                  # "start", "wander", "bite", ...
    instructions: list          # [IfGoto, Goto, Call, ...]



# Instrucciones


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



# Expresiones


@dataclass
class Number:
    """80, 6, 400, 15..."""
    value: int


@dataclass
class String:
    """"meat is back on the menu" (sin las comillas)"""
    value: str


@dataclass
class Identifier:
    """health, enemy_dist, GROUND, random, start..."""
    name: str


@dataclass
class BinaryOp:
    """a + b, a < b, a and b, etc."""
    op: str                     # "+", "-", "<", "==", "and", "or", ...
    left: object                # nodo de expresión
    right: object               # nodo de expresión


@dataclass
class UnaryOp:
    """-a, not a"""
    op: str                     # "-", "not"
    operand: object             # nodo de expresión


