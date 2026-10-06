from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # --- Palabras reservadas (las unicas del lenguaje, spec 2.3) ---
    IF    = auto()
    GOTO  = auto()
    AND   = auto()
    OR    = auto()
    NOT   = auto()

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
    LE      = auto()   # <=
    GT      = auto()   # >
    GE      = auto()   # >=
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
    value: str        
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"