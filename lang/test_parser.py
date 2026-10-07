# lang/test_parser.py
from lang.lexer import Lexer
from lang.parser import Parser
from lang.tokens import TokenType
from lang.errors import ParseError
from lang.ast_nodes import (
    SpeciesDef, Block, Label, IfGoto, Goto, Call, Assign,
)


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


def test_header():
    """parse_header: forma 'id valor' antes de 'start:' (spec 2.2)."""
    print("=== parse_header ===")

    # 1. cabecera completa, claves en orden libre
    src = ("creature Uruk\n"
           "lifespan 400\n"
           "faction isengard\n"
           "health 80\n"
           "vision 6\n"
           "start:\n")
    p = Parser(Lexer(src, "test.ins").tokenize(), "test.ins")
    entries = p.parse_header()
    print("  completa:", entries)
    assert entries == [
        ("creature", "Uruk", 1),
        ("lifespan", "400", 2),
        ("faction", "isengard", 3),
        ("health", "80", 4),
        ("vision", "6", 5),
    ]
    # el cursor queda apuntando a 'start:' sin consumirlo
    assert p.peek().type == TokenType.IDENT and p.peek().value == "start"
    assert p.peek(1).type == TokenType.COLON
    print("   OK, cursor en 'start:'")

    # 2. líneas en blanco de por medio: se saltan
    src = "creature Uruk\n\n\nhealth 80\n\nstart:\n"
    p = Parser(Lexer(src, "test.ins").tokenize(), "test.ins")
    entries = p.parse_header()
    print("  en blanco:", entries)
    assert entries == [("creature", "Uruk", 1), ("health", "80", 4)]
    print("   OK, líneas en blanco ignoradas")

    # 3. '-' delante de un número: forma válida (el rango es de semántica)
    src = "creature Uruk\nhealth -80\nstart:\n"
    p = Parser(Lexer(src, "test.ins").tokenize(), "test.ins")
    entries = p.parse_header()
    print("  negativo:", entries)
    assert entries == [("creature", "Uruk", 1), ("health", "-80", 2)]
    print("   OK, forma aceptada (fase 3 decide el rango)")

    # 4. errores: (fuente, fragmento que debe aparecer en el mensaje)
    casos = [
        ("faction isengard\nstart:\n", "primera línea de la cabecera"),
        ("start:\n",                   "primera línea no vacía"),
        ("creature\nstart:\n",         "se esperaba un valor"),
        ("creature Uruk\nhealth\nstart:\n", "se esperaba un valor"),
        ("creature Uruk\nhealth 80 90\nstart:\n", "fin de línea"),
        ("creature Uruk\nhealth 80 + 5\nstart:\n", "fin de línea"),
        ("creature Uruk\nhealth -vida\nstart:\n", "se esperaba un número"),
        ("creature Uruk\nif 5\nstart:\n", "clave de cabecera"),
        ("creature Uruk\n",            "falta la etiqueta"),
        ("",                           "falta la etiqueta"),
    ]
    for src, esperado in casos:
        print("  %-42r -> debe fallar" % src)
        p = Parser(Lexer(src, "test.ins").tokenize(), "test.ins")
        try:
            p.parse_header()
            raise AssertionError("debio fallar: %r" % src)
        except ParseError as e:
            assert esperado.lower() in str(e).lower(), \
                "esperaba %r en el mensaje, obtenido %r" % (esperado, str(e))
            print("     OK, ParseError:", e)

    print("=== parse_header OK ===\n")


def test_statement():
    """parse_statement: las5 formas de línea del cuerpo (spec 2.3)."""
    print("=== parse_statement ===")

    def parse(src):
        p = Parser(Lexer(src + "\n", "test.ins").tokenize(), "test.ins")
        return p, p.parse_statement()

    # 1. formas válidas -> nodo AST esperado
    casos = [
        ("wander:", "Label(name='wander', line=1)"),
        ("start:",  "Label(name='start', line=1)"),
        ("goto start", "Goto(label='start', line=1)"),
        ("if health < 20 goto flee",
         "IfGoto(condition=BinaryOp(op='<', left=Identifier(name='health', line=1), "
         "right=Number(value=20, line=1), line=1), label='flee', line=1)"),
        ("if see(x, y + 1) != GROUND goto wander",
         "IfGoto(condition=BinaryOp(op='!=', left=Call(name='see', args=["
         "Identifier(name='x', line=1), BinaryOp(op='+', "
         "left=Identifier(name='y', line=1), right=Number(value=1, line=1), "
         "line=1)], line=1), right=Identifier(name='GROUND', line=1), line=1), "
         "label='wander', line=1)"),
        ("steps = steps + 1",
         "Assign(name='steps', expr=BinaryOp(op='+', "
         "left=Identifier(name='steps', line=1), right=Number(value=1, line=1), "
         "line=1), line=1)"),
        ('say("meat is back")',
         "Call(name='say', args=[String(value='meat is back', line=1)], line=1)"),
        ("wait()", "Call(name='wait', args=[], line=1)"),
        ("move(-enemy_dx, -enemy_dy, 3)",
         "Call(name='move', args=[UnaryOp(op='-', "
         "operand=Identifier(name='enemy_dx', line=1), line=1), "
         "UnaryOp(op='-', operand=Identifier(name='enemy_dy', line=1), line=1), "
         "Number(value=3, line=1)], line=1)"),
    ]
    for src, esperado in casos:
        p, node = parse(src)
        print("  %-38r -> %s" % (src, node))
        assert str(node) == esperado, \
            "esperado %r, obtenido %r" % (esperado, str(node))
        # la línea se consume entera: quedamos en EOF
        assert p.peek().type == TokenType.EOF, "no consumió el NEWLINE final"
    print("   OK, formas válidas\n")

    # 2. errores: (fuente, fragmento del mensaje)
    casos_error = [
        ("foo + 1",           "línea no válida"),
        ("goto 5",            "nombre de una etiqueta"),
        ("goto",              "nombre de una etiqueta"),
        ("if health < 20 flee", "'goto'"),
        ("if",                "esperaba una expresion"),
        ("if health goto",    "nombre de una etiqueta"),
        ("move(1, 0, 1) x",   "fin de línea"),
        ("wander: x",         "fin de línea"),
        ("goto start + 1",    "fin de línea"),
        ("2 + 3",             "instrucción"),
    ]
    for src, esperado in casos_error:
        print("  %-38r -> debe fallar" % src)
        p = Parser(Lexer(src + "\n", "test.ins").tokenize(), "test.ins")
        try:
            p.parse_statement()
            raise AssertionError("debio fallar: %r" % src)
        except ParseError as e:
            assert esperado.lower() in str(e).lower(), \
                "esperaba %r en el mensaje, obtenido %r" % (esperado, str(e))
            print("     OK, ParseError:", e)

    print("=== parse_statement OK ===\n")


def test_species():
    """parse_species: archivo completo -> SpeciesDef (spec 2.1)."""
    print("=== parse_species ===")

    # 1. Uruk completo: cabecera + cuerpo con varias etiquetas
    uruk = """creature Uruk
faction isengard
health 80
vision 6
lifespan 400
start:
if health < 20 goto flee
goto start
flee:
move(-enemy_dx, -enemy_dy, 3)
goto start
"""
    p = Parser(Lexer(uruk, "uruk.ins").tokenize(), "uruk.ins")
    sp = p.parse_species()
    assert sp.name == "Uruk"
    assert sp.faction == "isengard"
    assert sp.health == 80
    assert sp.vision == 6
    assert sp.lifespan == 400
    assert sp.line == 1
    assert sp.header == [
        ("creature", "Uruk", 1),
        ("faction", "isengard", 2),
        ("health", "80", 3),
        ("vision", "6", 4),
        ("lifespan", "400", 5),
    ]
    assert set(sp.blocks.keys()) == {"start", "flee"}
    start = sp.blocks["start"]
    assert start.label == "start"
    assert len(start.instructions) == 2
    assert isinstance(start.instructions[0], IfGoto)
    assert start.instructions[0].label == "flee"
    assert isinstance(start.instructions[1], Goto)
    assert start.instructions[1].label == "start"
    flee = sp.blocks["flee"]
    assert len(flee.instructions) == 2
    assert isinstance(flee.instructions[0], Call)
    assert flee.instructions[0].name == "move"
    assert len(flee.instructions[0].args) == 3
    assert isinstance(flee.instructions[1], Goto)
    assert p.peek().type == TokenType.EOF  # consumió todo el archivo
    print("  OK, Uruk completo")

    # 2. mini con dos bloques (asignación + acción + goto)
    mini = """creature Mini
faction f
health 10
vision 1
lifespan 50
start:
steps = 0
wander:
move(1, 0, 1)
goto start
"""
    sp = Parser(Lexer(mini, "mini.ins").tokenize(), "mini.ins").parse_species()
    assert set(sp.blocks.keys()) == {"start", "wander"}
    assert len(sp.blocks["start"].instructions) == 1
    assert isinstance(sp.blocks["start"].instructions[0], Assign)
    assert len(sp.blocks["wander"].instructions) == 2
    assert isinstance(sp.blocks["wander"].instructions[0], Call)
    assert isinstance(sp.blocks["wander"].instructions[1], Goto)
    print("  OK, mini con dos bloques")

    # 3. solo la etiqueta start, sin instrucciones
    solo = """creature Solo
faction f
health 1
vision 1
lifespan 1
start:
"""
    sp = Parser(Lexer(solo, "solo.ins").tokenize(), "solo.ins").parse_species()
    assert sp.blocks["start"].instructions == []
    print("  OK, solo start:")

    # 4. claves faltantes: el parser no falla, deja '' / 0 (fase 3 decide)
    sin_faction = """creature X
health 5
start:
wait(1)
"""
    sp = Parser(Lexer(sin_faction, "x.ins").tokenize(), "x.ins").parse_species()
    assert sp.faction == ""
    assert sp.lifespan == 0
    assert sp.vision == 0
    print("  OK, claves faltantes -> '' / 0 (los completa fase 3)")

    # 5. líneas en blanco en el cuerpo: se saltan
    con_blancos = """creature B
faction f
health 1
vision 1
lifespan 1
start:

wait(1)

goto start
"""
    sp = Parser(Lexer(con_blancos, "b.ins").tokenize(), "b.ins").parse_species()
    assert len(sp.blocks["start"].instructions) == 2
    print("  OK, líneas en blanco en el cuerpo")

    # 6. etiqueta duplicada (una ya cerrada)
    dup = """creature D
faction f
health 1
vision 1
lifespan 1
start:
wait(1)
start:
goto start
"""
    try:
        Parser(Lexer(dup, "d.ins").tokenize(), "d.ins").parse_species()
        raise AssertionError("etiqueta duplicada no detectada")
    except ParseError as e:
        assert "duplicada" in str(e).lower()
        print("  OK, duplicada no consecutiva:", e)

    # 7. etiqueta duplicada consecutiva (la misma, seguida)
    cons = """creature C
faction f
health 1
vision 1
lifespan 1
start:
wander:
wander:
goto start
"""
    try:
        Parser(Lexer(cons, "c.ins").tokenize(), "c.ins").parse_species()
        raise AssertionError("etiqueta duplicada consecutiva no detectada")
    except ParseError as e:
        assert "duplicada" in str(e).lower()
        print("  OK, duplicada consecutiva:", e)

    print("=== parse_species OK ===\n")


def main():
    test_base()
    test_primary()
    test_unary()
    test_not()
    test_precedence()
    test_header()
    test_statement()
    test_species()


if __name__ == "__main__":
    main()
