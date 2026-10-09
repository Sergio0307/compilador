"""Catálogo del lenguaje Instinct (spec 2.4, 2.5 y 2.6).

Reúne en estructuras de datos todos los nombres que un archivo .ins puede
usar: las siete acciones básicas con su aridad, las funciones reservadas
see/name, las cinco constantes que devuelve see() y todas las percepciones.
Así el analizador semántico y el intérprete resuelven un nombre con una
consulta a un diccionario, sin cadenas de ifs (sección 5 de la spec).
"""

# Acciones básicas: nombre -> número de argumentos (spec 2.4).
# Extender el lenguaje = añadir una entrada aquí (y una clase Acción nueva).
ACTIONS = {
    "wait":      1,   # wait(n)
    "move":      3,   # move(dx, dy, speed)
    "attack":    3,   # attack(dx, dy, damage)
    "consume":   4,   # consume(dx, dy, damage, heal)
    "reproduce": 3,   # reproduce(dx, dy, health)
    "roar":      1,   # roar(value)
    "say":       1,   # say(value)
}

# Funciones reservadas: nombre -> número de argumentos (spec 2.6).
FUNCTIONS = {
    "see":  2,   # see(x, y)
    "name": 2,   # name(x, y)
}

# Constantes que devuelve see(): nombre -> valor (spec 2.6).
CONSTANTS = {
    "NONE":   -1,
    "GROUND":  0,
    "OBJECT":  1,
    "ALLY":    2,
    "ENEMY":   3,
}

# Percepciones de solo lectura (spec 2.6), agrupadas por dónde miran.

PERCEPTIONS_SELF = frozenset({
    "health", "age", "lifespan", "vision",
    "species", "faction", "x", "y",
    "terrain_here", "reserve_here",
})

PERCEPTIONS_WORLD = frozenset({
    "width", "height", "tick",
    "total_creatures", "total_allies", "total_enemies",
    "random",
})

PERCEPTIONS_NEAR = frozenset({
    "allies_near", "enemies_near", "objects_near",
    "enemy_dist", "enemy_dx", "enemy_dy",
    "ally_dist", "ally_dx", "ally_dy",
    "object_dist", "object_dx", "object_dy",
    "roars_near", "last_roar",
})

PERCEPTIONS = PERCEPTIONS_SELF | PERCEPTIONS_WORLD | PERCEPTIONS_NEAR

# Nombres a los que NO se puede asignar: percepciones y constantes (spec 2.3).
READONLY = PERCEPTIONS | set(CONSTANTS)
