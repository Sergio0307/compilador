from .tokens import Token, TokenType
from .errors import LexError


# Mapa de palabras reservadas → TokenType (las unicas del lenguaje)
KEYWORDS = {
    "if":    TokenType.IF,
    "goto":  TokenType.GOTO,
    "and":   TokenType.AND,
    "or":    TokenType.OR,
    "not":   TokenType.NOT,
}

# Símbolos de un solo carácter
SYMBOLS_1 = {
    ":": TokenType.COLON,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
}

# Símbolos de dos caracteres (se comprueban primero)
SYMBOLS_2 = {
    "==": TokenType.EQ,
    "!=": TokenType.NEQ,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<input>"):
        self.src      = source
        self.filename = filename
        self.pos      = 0
        self.line     = 1
        self.col      = 1
        self.tokens: list[Token] = []

    # ---------- utilidades de navegación ----------

    def peek(self, offset: int = 0) -> str:
        """Carácter actual (o el que está a `offset`), sin consumir."""
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def advance(self) -> str:
        """Consume y devuelve el carácter actual, actualizando línea/columna."""
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def at_end(self) -> bool:
        return self.pos >= len(self.src)

    def add(self, ttype: TokenType, value: str, line: int, col: int):
        self.tokens.append(Token(ttype, value, line, col))

    # ---------- bucle principal ----------

    def tokenize(self) -> list[Token]:
        while not self.at_end():
            ch = self.peek()

            # Espacios y tabs: se ignoran
            if ch in " \t\r":
                self.advance()
                continue

            # Comentarios: '#' hasta fin de línea (no consume el \n)
            if ch == "#":
                while not self.at_end() and self.peek() != "\n":
                    self.advance()
                continue

            # Salto de línea: token NEWLINE
            if ch == "\n":
                line, col = self.line, self.col
                self.advance()
                self.add(TokenType.NEWLINE, "\\n", line, col)
                continue

            # Número
            if ch.isdigit():
                self.read_number()
                continue

            # Identificador / palabra reservada
            if ch.isalpha() or ch == "_":
                self.read_ident()
                continue

            # String
            if ch == '"':
                self.read_string()
                continue

            # Símbolos (primero los de 2 chars)
            two = self.peek() + self.peek(1)
            if two in SYMBOLS_2:
                line, col = self.line, self.col
                self.advance(); self.advance()
                self.add(SYMBOLS_2[two], two, line, col)
                continue

            if ch in SYMBOLS_1:
                line, col = self.line, self.col
                self.advance()
                self.add(SYMBOLS_1[ch], ch, line, col)
                continue

            # Nada reconocido → error
            raise LexError(
                f"Carácter inesperado {ch!r}",
                line=self.line, col=self.col, filename=self.filename
            )

        #NEWLINE final (simplifica el parser)
        if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
            self.add(TokenType.NEWLINE, "\\n", self.line, self.col)

        self.add(TokenType.EOF, "", self.line, self.col)
        return self.tokens

    # ---------- lectores ----------

    def read_number(self):
        line, col = self.line, self.col
        start = self.pos
        while not self.at_end() and self.peek().isdigit():
            self.advance()
        # para decimales se añade '.')
        self.add(TokenType.NUMBER, self.src[start:self.pos], line, col)

    def read_ident(self):
        line, col = self.line, self.col
        start = self.pos
        while not self.at_end() and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.src[start:self.pos]
        ttype = KEYWORDS.get(text, TokenType.IDENT)
        self.add(ttype, text, line, col)

    def read_string(self):
        line, col = self.line, self.col
        self.advance()  # consume la comilla de apertura
        chars = []
        while not self.at_end() and self.peek() != '"':
            if self.peek() == "\n":
                raise LexError(
                    "String sin cerrar antes de fin de línea",
                    line=line, col=col, filename=self.filename
                )
            chars.append(self.advance())
        if self.at_end():
            raise LexError(
                "String sin cerrar",
                line=line, col=col, filename=self.filename
            )
        self.advance()  # consume la comilla de cierre
        self.add(TokenType.STRING, "".join(chars), line, col)