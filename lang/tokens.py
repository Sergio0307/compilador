from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # --- Palabras reservadas: cabecera ---
    CREATURE = auto()
    FACTION  = auto()
    HEALTH   = auto()
    VISION   = auto()
    LIFESPAN = auto()

    # --- Palabras reservadas: control ---
    IF    = auto()
    GOTO  = auto()
    AND   = auto()
    OR    = auto()
    NOT   = auto()

    # --- Built-ins ---
    MOVE      = auto()
    CONSUME   = auto()
    REPRODUCE = auto()
    SAY       = auto()
    ROAR      = auto()
    SEE       = auto()
    RANDOM    = auto()

    # --- Literales e identificadores ---
    NUMBER = auto()
    STRING = auto()
    IDENT  = auto()

    # --- Simbolos ---
    COLON   = auto()   # :
    LPAREN  = auto()   # (
    RPAREN  = auto()   # )
    COMMA   = auto()   # ,
    LT      = auto()   # <
    GT      = auto()   # >
    EQ      = auto()   # ==
    NEQ     = auto()   # !=
    PLUS    = auto()   # +
    MINUS   = auto()   # -
    STAR    = auto()   # *
    SLASH   = auto()   # /
    PERCENT = auto()   # %

    # --- Estructurales ---
    NEWLINE = auto()
    EOF     = auto()


@dataclass
class Token:
    type: TokenType
    value: str        # el texto original: "80", "health", "if"
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"