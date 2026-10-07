from lang.tokens import Token, TokenType
from lang.ast_nodes import (
    SpeciesDef, Block,
    Label, IfGoto, Goto, Call, Assign,
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

        # Despacho de líneas del cuerpo: tipo de línea -> método que la parsea
        self._handlers = {
            "label":  self.parse_label,
            "assign": self.parse_assign,
            "action": self.parse_action,
            "goto":   self.parse_goto,
            "if":     self.parse_if_goto,
        }


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


    # Utilidades de línea


    def skip_newlines(self):
        """Salta todos los NEWLINE seguidos (líneas en blanco)."""
        while self.match(TokenType.NEWLINE):
            pass

    def at_start_label(self):
        """¿Estamos en la etiqueta 'start:'? (IDENT 'start' + ':')"""
        return (self.peek().type == TokenType.IDENT
                and self.peek().value == "start"
                and self.peek(1).type == TokenType.COLON)


    # Cabecera (spec 2.2): líneas 'id valor' antes de 'start:'


    def parse_header_value(self):
        """Un valor de cabecera: nombre (IDENT o STRING) o número,
           con '-' opcional delante. Solo valida la FORMA: rangos,
           tipos y claves obligatorias son de la fase de semántica."""
        neg = self.match(TokenType.MINUS)
        tok = self.peek()
        if tok.type not in (TokenType.IDENT, TokenType.NUMBER, TokenType.STRING):
            raise ParseError(
                f"se esperaba un valor (nombre o número), se encontró "
                f"{tok.type.name} ({tok.value!r})",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        self.advance()
        if neg and tok.type != TokenType.NUMBER:
            raise ParseError(
                f"después de '-' se esperaba un número, se encontró ({tok.value!r})",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        return ("-" if neg else "") + tok.value

    def parse_header(self):
        """Cabecera: todo lo que aparece antes de la etiqueta 'start:'.
           Devuelve [(clave, valor, línea), ...] en orden de aparición.
           No valida las cinco claves obligatorias ni los rangos (fase 3).
           Deja el cursor apuntando a 'start:'."""
        entries = []
        while True:
            self.skip_newlines()

            # EOF sin haber visto 'start:' -> falta la etiqueta
            if self.check(TokenType.EOF):
                raise ParseError(
                    "falta la etiqueta 'start:'",
                    line=self.peek().line, col=self.peek().col,
                    filename=self.filename,
                )

            # Fin de la cabecera: aparece 'start:'
            if self.at_start_label():
                if not entries:
                    raise ParseError(
                        "la primera línea no vacía debe ser 'creature <nombre>'",
                        line=self.peek().line, col=self.peek().col,
                        filename=self.filename,
                    )
                break

            # Cada línea tiene la forma: id valor
            key = self.peek()
            if key.type != TokenType.IDENT:
                raise ParseError(
                    f"se esperaba una clave de cabecera (id valor), se encontró "
                    f"{key.type.name} ({key.value!r})",
                    line=key.line, col=key.col, filename=self.filename,
                )

            # La primera línea no vacía debe ser 'creature <nombre>'
            if not entries and key.value != "creature":
                raise ParseError(
                    f"la primera línea de la cabecera debe ser 'creature <nombre>', "
                    f"se encontró ({key.value!r})",
                    line=key.line, col=key.col, filename=self.filename,
                )

            self.advance()
            value = self.parse_header_value()
            entries.append((key.value, value, key.line))

            # Tras el valor solo puede venir fin de línea
            fin = self.peek()
            if fin.type not in (TokenType.NEWLINE, TokenType.EOF):
                raise ParseError(
                    f"se esperaba fin de línea, se encontró "
                    f"{fin.type.name} ({fin.value!r})",
                    line=fin.line, col=fin.col, filename=self.filename,
                )
            self.match(TokenType.NEWLINE)

        return entries


    # Instrucciones del cuerpo (spec 2.3): una línea = una instrucción


    def _classify(self):
        """Tipo de la línea del cuerpo. Si no encaja en ninguna forma
           válida, lanza ParseError. Sin efectos secundarios: no avanza."""
        tok = self.peek()

        if tok.type == TokenType.GOTO:
            return "goto"
        if tok.type == TokenType.IF:
            return "if"
        if tok.type == TokenType.IDENT:
            # Las tres formas que empiezan con IDENT se resuelven con datos,
            # no con ramas: COLON -> etiqueta, ASSIGN -> asignación, LPAREN -> acción
            kind = {
                TokenType.COLON:  "label",
                TokenType.ASSIGN: "assign",
                TokenType.LPAREN: "action",
            }.get(self.peek(1).type)
            if kind:
                return kind
            nxt = self.peek(1)
            raise ParseError(
                f"línea no válida: se esperaba ':', '=' o '(' después de "
                f"{tok.value!r}, se encontró {nxt.type.name} ({nxt.value!r})",
                line=nxt.line, col=nxt.col, filename=self.filename,
            )
        raise ParseError(
            f"se esperaba una instrucción (etiqueta, goto, if, asignación "
            f"o acción), se encontró {tok.type.name} ({tok.value!r})",
            line=tok.line, col=tok.col, filename=self.filename,
        )

    def parse_statement(self):
        """Una línea del cuerpo. Consume la línea completa, incluido su
           NEWLINE. Devuelve Label, Goto, IfGoto, Assign o Call."""
        node = self._handlers[self._classify()]()

        # Tras la instrucción solo puede venir fin de línea
        fin = self.peek()
        if fin.type not in (TokenType.NEWLINE, TokenType.EOF):
            raise ParseError(
                f"se esperaba fin de línea, se encontró "
                f"{fin.type.name} ({fin.value!r})",
                line=fin.line, col=fin.col, filename=self.filename,
            )
        self.match(TokenType.NEWLINE)
        return node

    def parse_label(self):
        """name: -> Label. Marca un punto de salto; no consume turno."""
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.COLON)
        return Label(name_tok.value, line=name_tok.line)

    def parse_goto(self):
        """goto name -> Goto. (Que la etiqueta exista: fase 3.)"""
        gt = self.expect(TokenType.GOTO)
        name_tok = self._expect_label_name()
        return Goto(name_tok.value, line=gt.line)

    def parse_if_goto(self):
        """if expr goto name -> IfGoto. La expresión se detiene sola en 'goto'
           porque es palabra reservada y ningún operador la incluye."""
        if_tok = self.expect(TokenType.IF)
        cond = self.parse_expression()
        if not self.check(TokenType.GOTO):
            tok = self.peek()
            raise ParseError(
                f"después de la expresión de 'if' se esperaba 'goto', "
                f"se encontró {tok.type.name} ({tok.value!r})",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        self.advance()
        name_tok = self._expect_label_name()
        return IfGoto(cond, name_tok.value, line=if_tok.line)

    def parse_action(self):
        """action(arg, ...) sola en su línea -> Call.
           (Que la acción exista y cuántos argumentos trae: fase 3.)"""
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.LPAREN)
        return self.parse_call_args(name_tok)

    def _expect_label_name(self):
        """El nombre de una etiqueta después de 'goto'."""
        if not self.check(TokenType.IDENT):
            tok = self.peek()
            raise ParseError(
                f"se esperaba el nombre de una etiqueta, "
                f"se encontró {tok.type.name} ({tok.value!r})",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        return self.advance()


    def parse_assign(self):
        """name = expr -> Assign. El '=' no puede ir dentro de una expresion
           ni encadenarse: x = y = 5 es error."""
        name_tok = self.expect(TokenType.IDENT)
        eq = self.expect(TokenType.ASSIGN)
        expr = self.parse_expression()
        if self.check(TokenType.ASSIGN):
            tok = self.peek()
            raise ParseError(
                "asignaciones encadenadas no permitidas (x = y = ...)",
                line=tok.line, col=tok.col, filename=self.filename,
            )
        return Assign(name_tok.value, expr, line=eq.line)


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
    
    
    
    