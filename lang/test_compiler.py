# lang/test_compiler.py
from lang.compiler import compile_species
from lang.errors import LexError, ParseError, SemanticError, SemanticErrors
from lang.ast_nodes import SpeciesDef


URUK = """creature Uruk
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


def test_valido():
    """Un archivo correcto atraviesa las tres fases y devuelve SpeciesDef."""
    print("=== válido ===")
    sp = compile_species(URUK, "uruk.ins")
    assert isinstance(sp, SpeciesDef)
    assert sp.name == "Uruk"
    assert set(sp.blocks.keys()) == {"start", "flee"}
    print("  OK, compila y devuelve SpeciesDef")
    print("=== válido OK ===\n")


def test_error_lexico():
    """El lexer para en el primer carácter inválido -> LexError."""
    print("=== error léxico ===")
    try:
        compile_species("creature Uruk\n$\n", "x.ins")
        raise AssertionError("debía lanzar LexError")
    except LexError as e:
        print("  OK, LexError:", e)
    print("=== error léxico OK ===\n")


def test_error_sintactico():
    """El parser para en la primera línea mal formada -> ParseError."""
    print("=== error sintáctico ===")
    try:
        compile_species("health 80\nstart:\n", "x.ins")
        raise AssertionError("debía lanzar ParseError")
    except ParseError as e:
        print("  OK, ParseError:", e)
    print("=== error sintáctico OK ===\n")


def test_semantic_errors():
    """SemanticErrors agrupa y formatea varios SemanticError juntos."""
    print("=== SemanticErrors ===")
    e1 = SemanticError("falta la clave 'health'", line=3, filename="x.ins")
    e2 = SemanticError("goto a etiqueta inexistente 'volar'", line=9, filename="x.ins")
    exc = SemanticErrors([e1, e2])
    texto = str(exc)
    assert "falta la clave 'health'" in texto
    assert "goto a etiqueta inexistente 'volar'" in texto
    assert exc.errors == [e1, e2]
    print(exc)
    print("=== SemanticErrors OK ===\n")


def main():
    test_valido()
    test_error_lexico()
    test_error_sintactico()
    test_semantic_errors()
    print("TODOS LOS TESTS DEL PIPELINE OK")


if __name__ == "__main__":
    main()
