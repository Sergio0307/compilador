"""Terreno del mundo: rejilla de casillas (reglas aprobadas del simulador).

Cada casilla tiene un terreno (GROUND transitable, ROCK obstáculo) y una
reserva de comida. Fuera de los límites del mapa hay ROCK: no se pisa, no
se ve como suelo y move() se detiene en él (el borde del mapa es roca).
"""

GROUND = 0
ROCK = 1


class Terrain:
    """Rejilla width x height de casillas con terreno y reserva."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._terrain = [[GROUND] * width for _ in range(height)]
        self._reserve = [[0] * width for _ in range(height)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def terrain_at(self, x, y):
        """Terreno de la casilla; fuera del mapa, ROCK."""
        if not self.in_bounds(x, y):
            return ROCK
        return self._terrain[y][x]

    def reserve_at(self, x, y):
        if not self.in_bounds(x, y):
            return 0
        return self._reserve[y][x]

    def is_walkable(self, x, y):
        return self.terrain_at(x, y) == GROUND

    def add_rock(self, x, y):
        if self.in_bounds(x, y):
            self._terrain[y][x] = ROCK

    def set_reserve(self, x, y, amount):
        if self.in_bounds(x, y):
            self._reserve[y][x] = amount
