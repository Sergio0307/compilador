# lang/test_parser.py
from lang.lexer import Lexer
from lang.parser import Parser
from lang.tokens import TokenType
from lang.errors import ParseError


def test_base():
    """Los 5 helpers: peek, advance, check, match, expect."""
    print("=== Base del parser ===")
    source = "creature Uruk\n"
    tokens = Lexer(source, "test.ins").tokenize()

    p = Parser(tokens, "test.ins")

    # 1. peek() -> estamos en IDENT("creature")
    print("1. peek:", p.peek())
    assert p.peek().type == TokenType.IDENT, "deberia estar en IDENT"
    assert p.peek().value == "creature"

    # 2. advance() -> consumimos "creature" y avanzamos
    tok = p.advance()
    print("2. advance:", tok)
    assert tok.type == TokenType.IDENT
    assert tok.value == "creature"

    # 3. peek() -> ahora estamos en IDENT("Uruk")
    print("3. peek:", p.peek())
    assert p.peek().type == TokenType.IDENT

    # 4. check() -> no consume
    print("4. check(IDENT):", p.check(TokenType.IDENT))
    assert p.check(TokenType.IDENT) is True
    print("   sigue en:", p.peek())
    assert p.peek().type == TokenType.IDENT, "check no debe consumir"

    # 5. match() -> consume si coincide
    tok = p.match(TokenType.IDENT)
    print("5. match(IDENT):", tok)
    assert tok is not None and tok.value == "Uruk"

    # 6. match() -> devuelve None si no coincide y no consume
    tok = p.match(TokenType.IF)
    print("6. match(IF):", tok)
    assert tok is None

    # 7. expect() -> OK cuando coincide
    tok = p.expect(TokenType.NEWLINE)
    print("7. expect(NEWLINE):", tok)
    assert tok.type == TokenType.NEWLINE

    # 8. expect() -> lanza ParseError cuando no coincide
    print("8. expect(IF): debe fallar")
    try:
        p.expect(TokenType.IF)
        print("   ERROR: no lanzo ParseError")
        raise AssertionError("expect deberia haber lanzado ParseError")
    except ParseError as e:
        print("   OK, ParseError:", e)

    print("=== Base del parser OK ===\n")


def test_primary():
    """parse_primary: numeros, strings, identificadores, parentesis."""
    print("=== parse_primary ===")
    casos = [
        ("42",         "Number(value=42, line=1)"),
        ('"hola"',     "String(value='hola', line=1)"),
        ("health",     "Identifier(name='health', line=1)"),
        ("random",     "Identifier(name='random', line=1)"),
        ("(42)",       "Number(value=42, line=1)"),
        ("enemy_dist", "Identifier(name='enemy_dist', line=1)"),
        ("vision",     "Identifier(name='vision', line=1)"),
        ("lifespan",   "Identifier(name='lifespan', line=1)"),
        ("see(1, 2)",  "Call(name='see', args=[Number(value=1, line=1), "
                       "Number(value=2, line=1)], line=1)"),
        ("name(1, 2)", "Call(name='name', args=[Number(value=1, line=1), "
                       "Number(value=2, line=1)], line=1)"),
        ("see(x, y + 1)",
                       "Call(name='see', args=[Identifier(name='x', line=1), "
                       "BinaryOp(op='+', left=Identifier(name='y', line=1), "
                       "right=Number(value=1, line=1), line=1)], line=1)"),
        ("f()",        "Call(name='f', args=[], line=1)"),
    ]
    for src, esperado in casos:
        tokens = Lexer(src + "\n", "test.ins").tokenize()
        p = Parser(tokens, "test.ins")
        expr = p.parse_primary()
        print("  %-12r -> %s" % (src, expr))
        assert str(expr) == esperado, \
            "esperado %r, obtenido %r" % (esperado, str(expr))
    print("=== parse_primary OK ===\n")


def test_unary():
    """parse_unary: -x y apilamiento del menos unario."""
    print("=== parse_unary ===")
    casos = [
        ("-42",     "UnaryOp(op='-', operand=Number(value=42, line=1), line=1)"),
        ("--5",     "UnaryOp(op='-', operand=UnaryOp(op='-', "
                    "operand=Number(value=5, line=1), line=1), line=1)"),
        ("(-5)",    "UnaryOp(op='-', operand=Number(value=5, line=1), line=1)"),
        ("-random", "UnaryOp(op='-', operand=Identifier(name='random', line=1), line=1)"),
        ("42",      "Number(value=42, line=1)"),
    ]
    for src, esperado in casos:
        tokens = Lexer(src + "\n", "test.ins").tokenize()
        p = Parser(tokens, "test.ins")
        expr = p.parse_unary()
        print("  %-12r -> %s" % (src, expr))
        assert str(expr) == esperado, \
            "esperado %r, obtenido %r" % (esperado, str(expr))

    # '-' solo debe fallar
    print("  %-12r -> debe fallar" % "-")
    tokens = Lexer("-\n", "test.ins").tokenize()
    p = Parser(tokens, "test.ins")
    try:
        p.parse_unary()
        raise AssertionError("'-' solo deberia lanzar ParseError")
    except ParseError as e:
        print("     OK, ParseError:", e)

    print("=== parse_unary OK ===\n")


def test_not():
    """'not' esta entre 'and' y las comparaciones (estilo Python)."""
    print("=== parse_not ===")
    casos = [
        ("not scared",
                    "UnaryOp(op='not', operand=Identifier(name='scared', line=1), line=1)"),
        ("not not x",
                    "UnaryOp(op='not', operand=UnaryOp(op='not', "
                    "operand=Identifier(name='x', line=1), line=1), line=1)"),
        ("not (x)", "UnaryOp(op='not', operand=Identifier(name='x', line=1), line=1)"),
        ("not 0",   "UnaryOp(op='not', operand=Number(value=0, line=1), line=1)"),
        ("not a < b",
                    "UnaryOp(op='not', operand=BinaryOp(op='<', "
                    "left=Identifier(name='a', line=1), "
                    "right=Identifier(name='b', line=1), line=1), line=1)"),
        ("not a and b",
                    "BinaryOp(op='and', left=UnaryOp(op='not', "
                    "operand=Identifier(name='a', line=1), line=1), "
                    "right=Identifier(name='b', line=1), line=1)"),
    ]
    for src, esperado in casos:
        tokens = Lexer(src + "\n", "test.ins").tokenize()
        p = Parser(tokens, "test.ins")
        expr = p.parse_expression()
        print("  %-14r -> %s" % (src, expr))
        assert str(expr) == esperado, \
            "esperado %r, obtenido %r" % (esperado, str(expr))

    # 'not' solo debe fallar
    print("  %-14r -> debe fallar" % "not")
    tokens = Lexer("not\n", "test.ins").tokenize()
    p = Parser(tokens, "test.ins")
    try:
        p.parse_expression()
        raise AssertionError("'not' solo deberia lanzar ParseError")
    except ParseError as e:
        print("     OK, ParseError:", e)

    print("=== parse_not OK ===\n")


def test_precedence():
    """Cadena completa: or -> and -> comparaciones -> + - -> * / % -> unary."""
    print("=== parse_expression (precedencia) ===")
    casos = [
        # * / % por encima de + -
        ("1 + 2 * 3",
         "BinaryOp(op='+', left=Number(value=1, line=1), right=BinaryOp(op='*', "
         "left=Number(value=2, line=1), right=Number(value=3, line=1), line=1), line=1)"),
        ("(1 + 2) * 3",
         "BinaryOp(op='*', left=BinaryOp(op='+', left=Number(value=1, line=1), "
         "right=Number(value=2, line=1), line=1), right=Number(value=3, line=1), line=1)"),
        # asociatividad por la izquierda
        ("1 + 2 + 3",
         "BinaryOp(op='+', left=BinaryOp(op='+', left=Number(value=1, line=1), "
         "right=Number(value=2, line=1), line=1), right=Number(value=3, line=1), line=1)"),
        ("1 - 2 - 3",
         "BinaryOp(op='-', left=BinaryOp(op='-', left=Number(value=1, line=1), "
         "right=Number(value=2, line=1), line=1), right=Number(value=3, line=1), line=1)"),
        # comparaciones por debajo de + - y por encima de and
        ("2 + 3 == 5",
         "BinaryOp(op='==', left=BinaryOp(op='+', left=Number(value=2, line=1), "
         "right=Number(value=3, line=1), line=1), right=Number(value=5, line=1), line=1)"),
        ("a < b and c > d",
         "BinaryOp(op='and', left=BinaryOp(op='<', left=Identifier(name='a', line=1), "
         "right=Identifier(name='b', line=1), line=1), right=BinaryOp(op='>', "
         "left=Identifier(name='c', line=1), right=Identifier(name='d', line=1), line=1), line=1)"),
        # and por debajo de comparaciones, or por debajo de and
        ("a or b and c",
         "BinaryOp(op='or', left=Identifier(name='a', line=1), right=BinaryOp(op='and', "
         "left=Identifier(name='b', line=1), right=Identifier(name='c', line=1), line=1), line=1)"),
        # comparadores nuevos
        ("a <= b or c >= d",
         "BinaryOp(op='or', left=BinaryOp(op='<=', left=Identifier(name='a', line=1), "
         "right=Identifier(name='b', line=1), line=1), right=BinaryOp(op='>=', "
         "left=Identifier(name='c', line=1), right=Identifier(name='d', line=1), line=1), line=1)"),
        # unary y not por encima de * / %
        ("-2 * 3",
         "BinaryOp(op='*', left=UnaryOp(op='-', operand=Number(value=2, line=1), line=1), "
         "right=Number(value=3, line=1), line=1)"),
        ("2 * -3",
         "BinaryOp(op='*', left=Number(value=2, line=1), right=UnaryOp(op='-', "
         "operand=Number(value=3, line=1), line=1), line=1)"),
        ("not a and b",
         "BinaryOp(op='and', left=UnaryOp(op='not', operand=Identifier(name='a', line=1), "
         "line=1), right=Identifier(name='b', line=1), line=1)"),
        # estilo Python: not por debajo de las comparaciones
        ("not health < 20",
         "UnaryOp(op='not', operand=BinaryOp(op='<', "
         "left=Identifier(name='health', line=1), "
         "right=Number(value=20, line=1), line=1), line=1)"),
        # comparacion encadenada estilo Python: a <= x < b  ->  (a <= x) and (x < b)
        ("0 <= x < 10",
         "BinaryOp(op='and', left=BinaryOp(op='<=', left=Number(value=0, line=1), "
         "right=Identifier(name='x', line=1), line=1), right=BinaryOp(op='<', "
         "left=Identifier(name='x', line=1), right=Number(value=10, line=1), line=1), line=1)"),
        # expresion del ejemplo del propio parser
        ("random % 3 - 1",
         "BinaryOp(op='-', left=BinaryOp(op='%', left=Identifier(name='random', line=1), "
         "right=Number(value=3, line=1), line=1), right=Number(value=1, line=1), line=1)"),
    ]
    for src, esperado in casos:
        tokens = Lexer(src + "\n", "test.ins").tokenize()
        p = Parser(tokens, "test.ins")
        expr = p.parse_expression()
        print("  %-16r -> %s" % (src, expr))
        assert str(expr) == esperado, \
            "esperado %r, obtenido %r" % (esperado, str(expr))
    print("=== parse_expression OK ===\n")


def main():
    test_base()
    test_primary()
    test_unary()
    test_not()
    test_precedence()


if __name__ == "__main__":
    main()
