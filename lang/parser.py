from lang.tokens import Token, TokenType
from lang.ast_nodes import (
    SpeciesDef, Block,
    IfGoto, Goto, Call,
    Number, String, Identifier, BinaryOp, UnaryOp,
)
from lang.errors import ParseError

class Parser:
    def __init__(self, tokens, filename="<input>"):
        self.tokens   = tokens
        self.pos      = 0
        self.filename = filename


    #manejo de la lista de tokens
    

    def peek(self, offset=0):
        """Mira el token actual (o el que está a `offset`), sin consumirlo."""
        i = self.pos + offset
        if i >= len(self.tokens):
            return self.tokens[-1]      # el último siempre es EOF
        return self.tokens[i]

    def advance(self):
        """Consume el token actual y lo devuelve."""
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def check(self, ttype):
        """¿El token actual es de este tipo? (no consume)"""
        return self.peek().type == ttype

    def match(self, ttype):
        """Si el token actual es de este tipo, lo consume y devuelve.
           Si no, devuelve None sin consumir nada."""
        if self.check(ttype):
            return self.advance()
        return None

    def expect(self, ttype):
        """Exige que el token actual sea de este tipo y lo consume.
           Si no lo es, lanza ParseError con línea y columna."""
        tok = self.peek()
        if tok.type != ttype:
            raise ParseError(
                f"se esperaba {ttype.name}, se encontró {tok.type.name} ({tok.value!r})",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        return self.advance()


