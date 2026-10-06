from lang.tokens import Token, TokenType
from lang.ast_nodes import (
    SpeciesDef, Block,
    IfGoto, Goto, Call,
    Number, String, Identifier, BinaryOp, UnaryOp,
)
from lang.errors import ParseError

COMPARISON_TYPES = (
    TokenType.LT, TokenType.LE,
    TokenType.GT, TokenType.GE,
    TokenType.EQ, TokenType.NEQ,
)

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
        """Nivel mas basico: numeros, strings, identificadores, llamadas, parentesis."""
        tok = self.peek()

        # Numero
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(int(tok.value), line=tok.line)

        # String
        if tok.type == TokenType.STRING:
            self.advance()
            return String(tok.value, line=tok.line)

        # Identificador: variable, percepcion o funcion (see, name, ...).
        # Un identificador seguido de '(' es una llamada: see(x, y), name(x, y)
        if tok.type == TokenType.IDENT:
            self.advance()
            if self.match(TokenType.LPAREN):
                return self.parse_call_args(tok)
            return Identifier(tok.value, line=tok.line)

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

    def parse_call_args(self, name_tok):
        """Consume los argumentos y el ')' de una llamada ya abierta.
           Admite lista vacia: f()"""
        args = []
        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expression())
        self.expect(TokenType.RPAREN)
        return Call(name_tok.value, args, line=name_tok.line)

    def parse_unary(self):
        """Operadores de prefijo: -x. Si no hay ninguno, es primaria.
           Llama a parse_unary (no a parse_primary) para que se apilen: - - 5."""
        tok = self.peek()

        if tok.type == TokenType.MINUS:
            self.advance()
            return UnaryOp("-", self.parse_unary(), line=tok.line)

        return self.parse_primary()

    # Expresiones: cadena de precedencia (de menor a mayor)
    # or -> and -> not -> comparaciones -> + - -> * / % -> unary -> primary
    # Estilo Python (spec 2.5): el encadenado a < b < c vale a < b and b < c

    def parse_or(self):
        left = self.parse_and()
        while self.check(TokenType.OR):
            op = self.advance()
            right = self.parse_and()
            left = BinaryOp("or", left, right, line=op.line)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.check(TokenType.AND):
            op = self.advance()
            right = self.parse_not()
            left = BinaryOp("and", left, right, line=op.line)
        return left

    def parse_not(self):
        """'not' esta entre 'and' y las comparaciones, como en Python:
           not a < b  ->  not (a < b)"""
        if self.check(TokenType.NOT):
            tok = self.advance()
            return UnaryOp("not", self.parse_not(), line=tok.line)
        return self.parse_comparison()

    def parse_comparison(self):
        """Comparaciones asociativas por la izquierda; encadenadas estilo Python:
           a < b < c  ->  (a < b) and (b < c)"""
        left = self.parse_term()
        if self.peek().type not in COMPARISON_TYPES:
            return left
        result = None
        while self.peek().type in COMPARISON_TYPES:
            op = self.advance()
            right = self.parse_term()
            cmp = BinaryOp(op.value, left, right, line=op.line)
            result = cmp if result is None else \
                BinaryOp("and", result, cmp, line=op.line)
            left = right
        return result

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_factor()
            left = BinaryOp(op.value, left, right, line=op.line)
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance()
            right = self.parse_unary()
            left = BinaryOp(op.value, left, right, line=op.line)
        return left

    def parse_expression(self):
        """Punto de entrada para cualquier expresion."""
        return self.parse_or()
    
    
    
    