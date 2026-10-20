"""Mundo de la simulación: criaturas, percepciones y las 7 acciones.

Cumple el contrato que lang/interpreter.py y lang/actions.py ya exigen:

    update_perceptions(creature)   snapshot por turno (spec 2.7.2)
    perception(creature, name)     valor del snapshot
    see / name_at                  funciones reservadas (spec 2.6)
    move / attack / consume / reproduce / roar / say

El mundo no interpreta programas: llama a Interpreter.run_turn y captura
RuntimeFault (el bicho muere de un ictus y queda en el log).

Reglas fijadas en el diseño:
 - radio de visión cuadrado de Chebyshev, sin línea de visión;
 - roars_near = rugidos de los últimos 3 ticks dentro del radio;
 - reproduce sin coste para el padre; reserve_here es informativa;
 - orden de turno = orden de creación; age +1 al final de su turno.
"""

import random

from lang.catalog import CONSTANTS
from lang.errors import RuntimeFault
from lang.interpreter import Interpreter, Program, CreatureExecution

from world.creature import Creature
from world.terrain import Terrain, ROCK


def _sign(value):
    """Signo direccional: -1, 0 o 1 (igual que las direcciones de move)."""
    return (value > 0) - (value < 0)


class World:
    def __init__(self, width=40, height=20, seed=None):
        self.terrain = Terrain(width, height)
        self.tick = 0
        self.creatures = []        # orden de creación = orden de turno
        self.roars = []            # [(tick, x, y, value), ...]
        self.log = []              # eventos: (tipo, tick, nombre, valor)
        self.interpreter = Interpreter()
        self.random = random.Random(seed)
        self._programs = {}        # id(SpeciesDef) -> Program (compartido)

    # ------------------------------------------------------------------
    # Población
    # ------------------------------------------------------------------

    def _program_of(self, species_def):
        """El Program se plana una vez por especie y lo comparten sus crías."""
        key = id(species_def)
        if key not in self._programs:
            self._programs[key] = Program.from_species(species_def)
        return self._programs[key]

    def add_creature(self, species_def, x, y):
        """Nace una criatura de `species_def` (SpeciesDef) en (x, y)."""
        creature = Creature(
            species_def,
            CreatureExecution(self._program_of(species_def)),
            x, y,
        )
        self.creatures.append(creature)
        return creature

    def free_cells(self):
        """Casillas transitables sin criatura viva."""
        ocupadas = {(c.x, c.y) for c in self.creatures if c.alive}
        return [
            (x, y)
            for y in range(self.terrain.height)
            for x in range(self.terrain.width)
            if self.terrain.is_walkable(x, y) and (x, y) not in ocupadas
        ]

    def creature_at(self, x, y):
        """Criatura viva que ocupa (x, y), o None."""
        for creature in self.creatures:
            if creature.alive and creature.x == x and creature.y == y:
                return creature
        return None

    def kill(self, creature, reason):
        creature.kill(reason)
        self.log.append(("muerte", self.tick, creature.species, reason))

    # ------------------------------------------------------------------
    # Rondas
    # ------------------------------------------------------------------

    def run_round(self):
        """Una ronda: cada criatura viva hace su turno, en orden de creación.

        Al cerrar la ronda avancen el tick y caducan los rugidos viejos.
        Devuelve la lista de vivas.
        """
        for creature in list(self.creatures):   # copia: reproduce añade
            if not creature.alive:
                continue
            try:
                self.interpreter.run_turn(creature, self)
            except RuntimeFault as fault:
                self.kill(creature, f"ictus: {fault.message}")
            if creature.alive:
                creature.age += 1
                if creature.age >= creature.lifespan:
                    self.kill(creature, "vejez")
        self.tick += 1
        self.roars = [r for r in self.roars if r[0] >= self.tick - 2]
        return [c for c in self.creatures if c.alive]

    # ------------------------------------------------------------------
    # Percepciones (spec 2.7.2)
    # ------------------------------------------------------------------

    @staticmethod
    def _distance(x1, y1, x2, y2):
        """Chebyshev: el radio de visión es un cuadrado."""
        return max(abs(x1 - x2), abs(y1 - y2))

    def _distance_to(self, creature, x, y):
        return self._distance(creature.x, creature.y, x, y)

    def _nearby_creatures(self, creature):
        return [
            other for other in self.creatures
            if other.alive and other is not creature
            and self._distance_to(creature, other.x, other.y) <= creature.vision
        ]

    def _rocks_in_vision(self, creature):
        v = creature.vision
        return [
            (x, y)
            for y in range(creature.y - v, creature.y + v + 1)
            for x in range(creature.x - v, creature.x + v + 1)
            if self.terrain.terrain_at(x, y) == ROCK
        ]

    def _nearest(self, creature, points):
        """(dist, dx, dy) hacia el más cercano; (-1, 0, 0) si no hay ninguno."""
        best = None
        for px, py in points:
            dist = self._distance_to(creature, px, py)
            if best is None or dist < best[0]:
                best = (dist, _sign(px - creature.x), _sign(py - creature.y))
        return best if best is not None else (-1, 0, 0)

    def update_perceptions(self, creature):
        """Snapshot de TODAS las percepciones al empezar su turno."""
        near = self._nearby_creatures(creature)
        allies = [o for o in near if o.faction == creature.faction]
        enemies = [o for o in near if o.faction != creature.faction]
        rocks = self._rocks_in_vision(creature)

        enemy_dist, enemy_dx, enemy_dy = self._nearest(
            creature, [(c.x, c.y) for c in enemies])
        ally_dist, ally_dx, ally_dy = self._nearest(
            creature, [(c.x, c.y) for c in allies])
        object_dist, object_dx, object_dy = self._nearest(creature, rocks)

        heard = [
            r for r in self.roars
            if r[0] >= self.tick - 2
            and self._distance_to(creature, r[1], r[2]) <= creature.vision
        ]

        creature.perceptions = {
            # yo (percepciones de la especie)
            "health": creature.health,
            "age": creature.age,
            "lifespan": creature.lifespan,
            "vision": creature.vision,
            "species": creature.species,
            "faction": creature.faction,
            "x": creature.x,
            "y": creature.y,
            "terrain_here": self.terrain.terrain_at(creature.x, creature.y),
            "reserve_here": self.terrain.reserve_at(creature.x, creature.y),
            # mundo
            "width": self.terrain.width,
            "height": self.terrain.height,
            "tick": self.tick,
            "total_creatures": sum(1 for c in self.creatures if c.alive),
            "total_allies": sum(
                1 for c in self.creatures
                if c.alive and c is not creature and c.faction == creature.faction),
            "total_enemies": sum(
                1 for c in self.creatures
                if c.alive and c is not creature and c.faction != creature.faction),
            "random": self.random.randint(0, 99),
            # cerca (radio de visión)
            "allies_near": len(allies),
            "enemies_near": len(enemies),
            "objects_near": len(rocks),
            "enemy_dist": enemy_dist,
            "enemy_dx": enemy_dx,
            "enemy_dy": enemy_dy,
            "ally_dist": ally_dist,
            "ally_dx": ally_dx,
            "ally_dy": ally_dy,
            "object_dist": object_dist,
            "object_dx": object_dx,
            "object_dy": object_dy,
            "roars_near": len(heard),
            "last_roar": heard[-1][3] if heard else "",
        }

    def perception(self, creature, name):
        """Valor del snapshot hecho al empezar el turno."""
        return creature.perceptions.get(name, 0)

    # ------------------------------------------------------------------
    # Funciones reservadas (spec 2.6): coordenadas ABSOLUTAS
    # ------------------------------------------------------------------

    def see(self, creature, x, y):
        """NONE si no se ve; si no, ALLY/ENEMY > OBJECT > GROUND."""
        if self._distance_to(creature, x, y) > creature.vision:
            return CONSTANTS["NONE"]
        other = self.creature_at(x, y)
        if other is not None and other is not creature:
            return CONSTANTS["ALLY"] if other.faction == creature.faction \
                else CONSTANTS["ENEMY"]
        if self.terrain.terrain_at(x, y) == ROCK:
            return CONSTANTS["OBJECT"]
        return CONSTANTS["GROUND"]

    def name_at(self, creature, x, y):
        """Nombre de lo que hay en (x, y); '' si no se ve o no hay nada."""
        if self._distance_to(creature, x, y) > creature.vision:
            return ""
        other = self.creature_at(x, y)
        if other is not None and other is not creature:
            return other.species
        if self.terrain.terrain_at(x, y) == ROCK:
            return "Rock"
        return ""

    # ------------------------------------------------------------------
    # Acciones (lang/actions.py llama a esto)
    # ------------------------------------------------------------------

    def move(self, creature, dx, dy, speed):
        """Avanza hasta `speed` casillas; se para ante roca, borde o bicho."""
        for _ in range(max(0, speed)):
            nx, ny = creature.x + dx, creature.y + dy
            if not self.terrain.is_walkable(nx, ny):
                break
            if self.creature_at(nx, ny) is not None:
                break
            creature.x, creature.y = nx, ny

    def _hurt(self, creature, dx, dy, damage, kind):
        """Daña a quien haya en la casilla relativa; (0,0) es la propia."""
        target = self.creature_at(creature.x + dx, creature.y + dy)
        if target is None:
            return                      # golpe al aire
        target.health = min(target.max_health, target.health - damage)
        if target.health <= 0:
            target.health = 0
            self.kill(target, f"{kind} de {creature.species}")

    def attack(self, creature, dx, dy, damage):
        self._hurt(creature, dx, dy, damage, "ataque")

    def consume(self, creature, dx, dy, damage, heal):
        """Como attack y además el atacante gana `heal` de vida (clamp)."""
        self._hurt(creature, dx, dy, damage, "consume")
        if not creature.alive:
            return
        creature.health = max(
            0, min(creature.max_health, creature.health + heal))
        if creature.health == 0:
            self.kill(creature, "consume con cura no positiva")

    def reproduce(self, creature, dx, dy, health):
        """Cría en la casilla adyacente si está libre; sin coste al padre."""
        nx, ny = creature.x + dx, creature.y + dy
        if not self.terrain.is_walkable(nx, ny):
            return
        if self.creature_at(nx, ny) is not None:
            return
        child = self.add_creature(creature.species_def, nx, ny)
        child.health = max(1, min(creature.max_health, health))
        self.log.append(("nacimiento", self.tick, child.species, (nx, ny)))

    def roar(self, creature, value):
        """Registra el rugido: lo oyen quienes están en su radio de visión."""
        self.roars.append((self.tick, creature.x, creature.y, value))
        self.log.append(("rugido", self.tick, creature.species, value))

    def say(self, creature, value):
        """No toca el mundo: va al log (lo imprime la CLI)."""
        self.log.append(("dice", self.tick, creature.species, value))
