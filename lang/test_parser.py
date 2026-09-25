# lang/test_parser.py
from lang.lexer import Lexer
from lang.parser import Parser
from lang.tokens import TokenType
from lang.errors import ParseError


def main():
    source = "creature Uruk\n"
    tokens = Lexer(source, "test.ins").tokenize()

    p = Parser(tokens, "test.ins")

    # 1. peek() → estamos en CREATURE
    print("1. peek:", p.peek())
    assert p.peek().type == TokenType.CREATURE, "debería estar en CREATURE"

    # 2. advance() → consumimos CREATURE y avanzamos
    tok = p.advance()
    print("2. advance:", tok)
    assert tok.type == TokenType.CREATURE

    # 3. peek() → ahora estamos en IDENT("Uruk")
    print("3. peek:", p.peek())
    assert p.peek().type == TokenType.IDENT

    # 4. check() → no consume
    print("4. check(IDENT):", p.check(TokenType.IDENT))
    assert p.check(TokenType.IDENT) is True
    print("   sigue en:", p.peek())
    assert p.peek().type == TokenType.IDENT, "check no debe consumir"

    # 5. match() → consume si coincide
    tok = p.match(TokenType.IDENT)
    print("5. match(IDENT):", tok)
    assert tok is not None and tok.value == "Uruk"

    # 6. match() → devuelve None si no coincide y no consume
    tok = p.match(TokenType.IF)
    print("6. match(IF):", tok)
    assert tok is None

    # 7. expect() → OK cuando coincide
    tok = p.expect(TokenType.NEWLINE)
    print("7. expect(NEWLINE):", tok)
    assert tok.type == TokenType.NEWLINE

    # 8. expect() → lanza ParseError cuando no coincide
    print("8. expect(IF) → debe fallar:")
    try:
        p.expect(TokenType.IF)
        print("   ERROR: no lanzó ParseError")
    except ParseError as e:
        print("   OK, ParseError:", e)

    print("\n=== Base del parser OK ===")


if __name__ == "__main__":
    main()