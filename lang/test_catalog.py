# lang/test_catalog.py
from lang.catalog import (
    ACTIONS, FUNCTIONS, CONSTANTS,
    PERCEPTIONS, PERCEPTIONS_SELF, PERCEPTIONS_WORLD, PERCEPTIONS_NEAR,
    READONLY,
)


def test_actions():
    """Las siete acciones básicas con sus aridades exactas (spec 2.4)."""
    print("=== actions ===")
    esperado = {
        "wait":      1,
        "move":      3,
        "attack":    3,
        "consume":   4,
        "reproduce": 3,
        "roar":      1,
        "say":       1,
    }
    assert ACTIONS == esperado, "catálogo de acciones incorrecto: %r" % (ACTIONS,)
    assert len(ACTIONS) == 7
    print("  OK, 7 acciones:", ACTIONS)
    print("=== actions OK ===\n")


def test_functions():
    """Las funciones reservadas see/name con aridad 2 (spec 2.6)."""
    print("=== functions ===")
    assert FUNCTIONS == {"see": 2, "name": 2}, FUNCTIONS
    print("  OK, see/name:", FUNCTIONS)
    print("=== functions OK ===\n")


def test_constants():
    """Las cinco constantes de see() con sus valores (spec 2.6)."""
    print("=== constants ===")
    esperado = {"NONE": -1, "GROUND": 0, "OBJECT": 1, "ALLY": 2, "ENEMY": 3}
    assert CONSTANTS == esperado, CONSTANTS
    print("  OK, 5 constantes:", CONSTANTS)
    print("=== constants OK ===\n")


def test_perceptions():
    """Todas las percepciones, agrupadas por dónde miran (spec 2.6)."""
    print("=== perceptions ===")
    assert len(PERCEPTIONS_SELF) == 10, len(PERCEPTIONS_SELF)
    assert len(PERCEPTIONS_WORLD) == 7, len(PERCEPTIONS_WORLD)
    assert len(PERCEPTIONS_NEAR) == 14, len(PERCEPTIONS_NEAR)
    assert len(PERCEPTIONS) == 31, len(PERCEPTIONS)

    assert not (PERCEPTIONS_SELF & PERCEPTIONS_WORLD)
    assert not (PERCEPTIONS_SELF & PERCEPTIONS_NEAR)
    assert not (PERCEPTIONS_WORLD & PERCEPTIONS_NEAR)

    for nombre in ("health", "enemy_dist", "random", "last_roar", "reserve_here"):
        assert nombre in PERCEPTIONS, nombre
    print("  OK, 31 percepciones (self=10, world=7, near=14)")
    print("=== perceptions OK ===\n")


def test_no_solapamiento():
    """Ningún nombre pertenece a dos categorías del catálogo."""
    print("=== sin solapamiento ===")
    grupos = [
        ("acciones", set(ACTIONS)),
        ("funciones", set(FUNCTIONS)),
        ("constantes", set(CONSTANTS)),
        ("percepciones", set(PERCEPTIONS)),
    ]
    for i in range(len(grupos)):
        for j in range(i + 1, len(grupos)):
            nombre_i, conjunto_i = grupos[i]
            nombre_j, conjunto_j = grupos[j]
            repetidos = conjunto_i & conjunto_j
            assert not repetidos, "%s y %s comparten %r" % (nombre_i, nombre_j, repetidos)
    print("  OK, categorías disjuntas")
    print("=== sin solapamiento OK ===\n")


def test_readonly():
    """READONLY = percepciones + constantes (no se puede asignar a ellos)."""
    print("=== readonly ===")
    assert READONLY == (set(PERCEPTIONS) | set(CONSTANTS))
    assert "health" in READONLY and "GROUND" in READONLY
    assert "move" not in READONLY and "home_x" not in READONLY
    print("  OK, READONLY tiene %d nombres" % len(READONLY))
    print("=== readonly OK ===\n")


def main():
    test_actions()
    test_functions()
    test_constants()
    test_perceptions()
    test_no_solapamiento()
    test_readonly()
    print("TODOS LOS TESTS DEL CATÁLOGO OK")


if __name__ == "__main__":
    main()
