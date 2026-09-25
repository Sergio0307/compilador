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


    # Expresiones: nivel primario (atomos)


    def parse_primary(self):
        """Nivel mas basico: numeros, strings, identificadores, parentesis."""
        tok = self.peek()

        # Numero
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(int(tok.value), line=tok.line)

        # String
        if tok.type == TokenType.STRING:
            self.advance()
            return String(tok.value, line=tok.line)

        # Identificador cualquiera (enemy_dist, GROUND, start, ...)
        if tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(tok.value, line=tok.line)

        # 'random' es un built-in que se comporta como valor:
        # se usa en expresiones como "random % 3"
        if tok.type == TokenType.RANDOM:
            self.advance()
            return Identifier("random", line=tok.line)

        # 'health', 'vision' y 'lifespan' son palabras clave por el lexer
        # pero tambien variables legibles de la criatura ("if health < 30")
        if tok.type in (TokenType.HEALTH, TokenType.VISION, TokenType.LIFESPAN):
            self.advance()
            return Identifier(tok.value, line=tok.line)

        # 'see(x, y)' es un built-in con parentesis obligatorios
        if tok.type == TokenType.SEE:
            self.advance()
            self.expect(TokenType.LPAREN)
            x = self.parse_expression()
            self.expect(TokenType.COMMA)
            y = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return Call("see", [x, y], line=tok.line)

        # Parentesis: (expr)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # Nada de lo anterior -> error
        raise ParseError(
            f"se esperaba una expresion, se encontro {tok.type.name} ({tok.value!r})",
            line=tok.line, col=tok.col, filename=self.filename,
        )

    def parse_unary(self):
        """Operadores de prefijo: -x, not x. Si no hay ninguno, es primaria.

           Llama a parse_unary (no a parse_primary) para que los operadores
           se apilen: - - 5, not not x."""
        tok = self.peek()

        if tok.type == TokenType.MINUS:
            self.advance()
            return UnaryOp("-", self.parse_unary(), line=tok.line)

        if tok.type == TokenType.NOT:
            self.advance()
            return UnaryOp("not", self.parse_unary(), line=tok.line)

        return self.parse_primary()

    def parse_expression(self):
        """Punto de entrada para cualquier expresion.
           De momento delega en parse_unary; luego subiremos a parse_or."""
        return self.parse_unary()

