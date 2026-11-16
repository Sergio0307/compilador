# lang/test_lexer.py
"""Tests del lexer con pytest."""

import pytest
from lang.lexer import Lexer
from lang.tokens import TokenType
from lang.errors import LexError


def test_lexer_basico():
    """Tokens básicos: número, identificador, símbolos."""
    src = "health 42\n"
    tokens = Lexer(src, "test.ins").tokenize()
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].value == "health"
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == "42"
    assert tokens[2].type == TokenType.NEWLINE
    assert tokens[2].value == ""  # 1.3: NEWLINE vacío
    assert tokens[3].type == TokenType.EOF


def test_lexer_numero_unicode_rechazado():
    """1.1: dígitos Unicode (², ٣) deben lanzar LexError."""
    for bad in ["²", "٣", "¼"]:
        src = f"health {bad}\n"
        with pytest.raises(LexError) as exc:
            Lexer(src, "test.ins").tokenize()
        assert "inesperado" in str(exc.value).lower()


def test_lexer_exclamacion_sugiere_diferente():
    """1.2: '!' solo sugiere '!='."""
    src = "!\n"
    with pytest.raises(LexError) as exc:
        Lexer(src, "test.ins").tokenize()
    assert "!=" in str(exc.value)


def test_lexer_exclamacion_igual_es_neq():
    """'!=' produce token NEQ."""
    src = "!=\n"
    tokens = Lexer(src, "test.ins").tokenize()
    assert tokens[0].type == TokenType.NEQ
    assert tokens[0].value == "!="


def test_lexer_newline_valor_vacio():
    """1.3: NEWLINE tiene valor vacío."""
    src = "\n"
    tokens = Lexer(src, "test.ins").tokenize()
    assert tokens[0].type == TokenType.NEWLINE
    assert tokens[0].value == ""


def test_lexer_peek_offset_negativo():
    """1.4: peek(offset<0) lanza ValueError."""
    lexer = Lexer("abc", "test.ins")
    with pytest.raises(ValueError):
        lexer.peek(-1)


def test_lexer_init_valida_source():
    """1.6: Lexer rechaza source no-str."""
    with pytest.raises(TypeError):
        Lexer(None, "test.ins")
    with pytest.raises(TypeError):
        Lexer(123, "test.ins")
    with pytest.raises(TypeError):
        Lexer(b"bytes", "test.ins")


def test_lexer_string_multilinea_error():
    """String sin cerrar antes de \n lanza error con línea/columna."""
    src = '"hola\n'
    with pytest.raises(LexError) as exc:
        Lexer(src, "test.ins").tokenize()
    assert "sin cerrar" in str(exc.value).lower()
    assert exc.value.line == 1


def test_lexer_palabras_reservadas():
    """if, goto, and, or, not son tokens dedicados."""
    src = "if goto and or not\n"
    tokens = Lexer(src, "test.ins").tokenize()
    assert tokens[0].type == TokenType.IF
    assert tokens[1].type == TokenType.GOTO
    assert tokens[2].type == TokenType.AND
    assert tokens[3].type == TokenType.OR
    assert tokens[4].type == TokenType.NOT


def test_lexer_simbolos_dos_chars():
    """==, !=, <=, >= se reconocen como un token."""
    src = "== != <= >=\n"
    tokens = Lexer(src, "test.ins").tokenize()
    assert tokens[0].type == TokenType.EQ
    assert tokens[1].type == TokenType.NEQ
    assert tokens[2].type == TokenType.LE
    assert tokens[3].type == TokenType.GE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])