# lang/test_semantics.py
from lang.lexer import Lexer
from lang.parser import Parser
from lang.semantics import SemanticAnalyzer
from lang.compiler import compile_species
from lang.errors import SemanticErrors


def build(header_lines, body="start:\nwait(1)\n"):
    """Arma un .ins: cabecera (lista de líneas) + cuerpo."""
    return "".join(line + "\n" for line in header_lines) + body


def analizar(src, filename="t.ins"):
    """Corre léxica + sintáctica + semántica y devuelve la lista de errores."""
    species = Parser(Lexer(src, filename).tokenize(), filename).parse_species()
    return SemanticAnalyzer(filename).analyze(species)


VALID = ["creature X", "faction f", "health 10", "vision 1", "lifespan 50"]


def test_cabecera_valida():
    """Las cinco claves correctas -> sin errores."""
    print("=== cabecera válida ===")
    errors = analizar(build(VALID))
    assert errors == [], errors
    print("  OK, 0 errores")
    print("=== cabecera válida OK ===\n")


def test_faltante_una():
    """Falta una clave obligatoria -> se rechaza (decisión A)."""
    print("=== falta una clave ===")
    header = ["creature X", "health 10", "vision 1", "lifespan 50"]  # falta faction
    errors = analizar(build(header))
    assert len(errors) == 1, errors
    assert "faction" in str(errors[0])
    assert errors[0].line == 1  # línea de 'creature'
    print("  OK:", errors[0])
    print("=== falta una clave OK ===\n")


def test_faltan_varias():
    """Faltan varias claves -> se acumulan todos los errores."""
    print("=== faltan varias ===")
    errors = analizar(build(["creature X"]))  # faltan faction, health, vision, lifespan
    assert len(errors) == 4, errors
    texto = " ".join(str(e) for e in errors)
    for key in ("faction", "health", "vision", "lifespan"):
        assert key in texto, key
    assert all(e.line == 1 for e in errors)
    print("  OK, 4 errores acumulados")
    print("=== faltan varias OK ===\n")


def test_desconocida():
    """Clave que no existe -> error con su línea."""
    print("=== clave desconocida ===")
    header = VALID + ["color green"]
    errors = analizar(build(header))
    assert len(errors) == 1, errors
    assert "color" in str(errors[0]) and "desconocida" in str(errors[0])
    assert errors[0].line == 6
    print("  OK:", errors[0])
    print("=== clave desconocida OK ===\n")


def test_duplicada():
    """Clave repetida -> error en la línea de la repetición."""
    print("=== clave duplicada ===")
    header = ["creature X", "faction f", "health 10", "health 20", "vision 1", "lifespan 50"]
    errors = analizar(build(header))
    assert len(errors) == 1, errors
    assert "duplicada" in str(errors[0]) and "health" in str(errors[0])
    assert errors[0].line == 4
    print("  OK:", errors[0])
    print("=== clave duplicada OK ===\n")


def test_rangos():
    """health > 0, vision >= 1, lifespan > 0."""
    print("=== rangos ===")
    casos = [
        (["creature X", "faction f", "health 0",   "vision 1", "lifespan 50"], "health"),
        (["creature X", "faction f", "health 10",  "vision 0", "lifespan 50"], "vision"),
        (["creature X", "faction f", "health 10",  "vision 1", "lifespan -5"], "lifespan"),
    ]
    for header, clave in casos:
        errors = analizar(build(header))
        assert len(errors) == 1, errors
        assert clave in str(errors[0]) and ">=" in str(errors[0]), errors[0]
        print("  OK:", errors[0])
    print("=== rangos OK ===\n")


def test_creature_nombre():
    """creature/faction deben ser nombre, no número."""
    print("=== creature/faction nombre ===")
    errors = analizar(build(["creature 80", "faction f", "health 10", "vision 1", "lifespan 50"]))
    assert len(errors) == 1 and "nombre" in str(errors[0]), errors
    print("  OK:", errors[0])

    errors = analizar(build(["creature X", "faction 7", "health 10", "vision 1", "lifespan 50"]))
    assert len(errors) == 1 and "faction" in str(errors[0]), errors
    print("  OK:", errors[0])
    print("=== creature/faction nombre OK ===\n")


def test_numero_esperado():
    """health/vision/lifespan deben ser número (no un nombre)."""
    print("=== número esperado ===")
    errors = analizar(build(["creature X", "faction f", "health abc", "vision 1", "lifespan 50"]))
    assert len(errors) == 1 and "número" in str(errors[0]), errors
    print("  OK:", errors[0])
    print("=== número esperado OK ===\n")


def test_string_comillas():
    """Un valor entre comillas se acepta como nombre (sin las comillas)."""
    print("=== valor entre comillas ===")
    header = ['creature X', 'faction "isengard"', "health 10", "vision 1", "lifespan 50"]
    errors = analizar(build(header))
    assert errors == [], errors
    print("  OK, aceptado como nombre")
    print("=== valor entre comillas OK ===\n")


def test_via_compiler():
    """compile_species lanza SemanticErrors con TODOS los fallos juntos."""
    print("=== vía compile_species ===")
    src = build(["creature X", "health 0"])  # faltan faction, vision, lifespan + rango
    try:
        compile_species(src, "x.ins")
        raise AssertionError("debía lanzar SemanticErrors")
    except SemanticErrors as e:
        assert len(e.errors) == 4, e.errors
        texto = str(e)
        print(texto)
    print("=== vía compile_species OK ===\n")


def test_goto_valido():
    """Saltos hacia adelante y hacia atrás a etiquetas existentes -> sin errores."""
    print("=== goto válido ===")
    body = "start:\ngoto fin\nfin:\nwait(1)\ngoto start\n"
    errors = analizar(build(VALID, body))
    assert errors == [], errors
    print("  OK, saltos válidos")
    print("=== goto válido OK ===\n")


def test_goto_inexistente():
    """goto a una etiqueta que no existe -> error con línea y nombre."""
    print("=== goto inexistente ===")
    body = "start:\ngoto volar\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 1, errors
    assert "volar" in str(errors[0]) and "inexistente" in str(errors[0])
    assert "start" in str(errors[0])
    assert errors[0].line == 7  # 5 líneas de cabecera + 'start:' + el goto
    print("  OK:", errors[0])
    print("=== goto inexistente OK ===\n")


def test_if_goto_inexistente():
    """if ... goto a una etiqueta que no existe -> error."""
    print("=== if-goto inexistente ===")
    body = "start:\nif health < 10 goto curar\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 1, errors
    assert "curar" in str(errors[0]), errors
    print("  OK:", errors[0])
    print("=== if-goto inexistente OK ===\n")


def test_varios_saltos_rotos():
    """Varios saltos rotos -> se acumulan todos."""
    print("=== varios saltos rotos ===")
    body = "start:\ngoto a\nif x > 0 goto b\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 2, errors
    texto = " ".join(str(e) for e in errors)
    assert "'a'" in texto and "'b'" in texto, texto
    print("  OK, 2 errores acumulados")
    print("=== varios saltos rotos OK ===\n")


def test_saltos_via_compiler():
    """compile_species junta un fallo de cabecera y un goto roto."""
    print("=== saltos vía compile_species ===")
    header = ["creature X", "faction f", "health 10", "vision 1"]  # falta lifespan
    src = build(header, "start:\ngoto nope\n")
    try:
        compile_species(src, "x.ins")
        raise AssertionError("debía lanzar SemanticErrors")
    except SemanticErrors as e:
        assert len(e.errors) == 2, e.errors
        print(str(e))
    print("=== saltos vía compile_species OK ===\n")


def test_asignacion_variable():
    """Asignar a una variable propia (nueva) está permitido."""
    print("=== asignación a variable ===")
    body = "start:\nhome_x = 5\ngoto start\n"
    errors = analizar(build(VALID, body))
    assert errors == [], errors
    print("  OK, variable propia permitida")
    print("=== asignación a variable OK ===\n")


def test_asignacion_percepcion():
    """Asignar a una percepción -> error."""
    print("=== asignación a percepción ===")
    body = "start:\nhealth = 5\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 1, errors
    assert "percepción" in str(errors[0]) and "health" in str(errors[0])
    assert errors[0].line == 7  # 5 de cabecera + 'start:' + la asignación
    print("  OK:", errors[0])
    print("=== asignación a percepción OK ===\n")


def test_asignacion_constante():
    """Asignar a una constante -> error."""
    print("=== asignación a constante ===")
    body = "start:\nGROUND = 1\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 1, errors
    assert "constante" in str(errors[0]) and "GROUND" in str(errors[0])
    print("  OK:", errors[0])
    print("=== asignación a constante OK ===\n")


def test_asignaciones_acumuladas():
    """Varias asignaciones prohibidas -> se acumulan."""
    print("=== asignaciones acumuladas ===")
    body = "start:\nhealth = 5\nenemy_dist = 0\nGROUND = 1\n"
    errors = analizar(build(VALID, body))
    assert len(errors) == 3, errors
    print("  OK, 3 errores acumulados")
    print("=== asignaciones acumuladas OK ===\n")


def test_asignacion_accion_permitida():
    """La spec solo prohíbe percepciones y constantes: 'move = 5' se permite."""
    print("=== asignación a nombre de acción ===")
    body = "start:\nmove = 5\n"
    errors = analizar(build(VALID, body))
    assert errors == [], errors
    print("  OK, permitido (fiel a la spec)")
    print("=== asignación a nombre de acción OK ===\n")


def test_asignacion_via_compiler():
    """compile_species junta un fallo de cabecera y una asignación prohibida."""
    print("=== asignación vía compile_species ===")
    header = ["creature X", "faction f", "health 10", "vision 1"]  # falta lifespan
    src = build(header, "start:\nhealth = 3\n")
    try:
        compile_species(src, "x.ins")
        raise AssertionError("debía lanzar SemanticErrors")
    except SemanticErrors as e:
        assert len(e.errors) == 2, e.errors
        print(str(e))
    print("=== asignación vía compile_species OK ===\n")


def main():
    test_cabecera_valida()
    test_faltante_una()
    test_faltan_varias()
    test_desconocida()
    test_duplicada()
    test_rangos()
    test_creature_nombre()
    test_numero_esperado()
    test_string_comillas()
    test_via_compiler()
    test_goto_valido()
    test_goto_inexistente()
    test_if_goto_inexistente()
    test_varios_saltos_rotos()
    test_saltos_via_compiler()
    test_asignacion_variable()
    test_asignacion_percepcion()
    test_asignacion_constante()
    test_asignaciones_acumuladas()
    test_asignacion_accion_permitida()
    test_asignacion_via_compiler()
    print("TODOS LOS TESTS DE SEMÁNTICA OK")


if __name__ == "__main__":
    main()
