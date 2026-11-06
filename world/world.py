"""Mundo de la simulación: criaturas, percepciones y las 7 acciones.

Cumple el contrato que lang/interpreter.py y lang/actions.py ya exigen:

    update_perceptions(creature)   snapshot por turno (spec 2.7.2)
    perception(creature, name)     valor del snapshot
    see / name_at                  funciones reservadas (spec 2.6)
    move / attack / consume / reproduce / roar / say

El mundo no interpreta programas: llama a Interpreter.run_turn y captura
RuntimeFault (el bicho muere de un ictus y queda en el log).

El tablero (terrenos, objetos, ocupación) vive en WorldMap. World se
encarga del bucle de turnos y de traducir las acciones a operaciones
sobre ese tablero.

Reglas fijadas en el diseño:
 - radio de visión cuadrado de Chebyshev, sin línea de visión;
 - "roars_near" = rugidos del tick anterior dentro del radio;
 - "reproduce" gasta vida a la madre y la cría nace sin tope;
 - orden de turno = sorteo al azar en cada tick;
 - leyes naturales al cierre del tick: vida -1, edad +1, verificar
   muertes, regenerar terrenos y retirar objetos agotados.
"""

import random

from lang.errors import RuntimeFault
from lang.interpreter import CreatureExecution, Interpreter, Program
from world.creature import Creature
from world.entities import WorldObject
from world.map import WorldMap


def _sign(value):
    """Signo direccional: -1, 0 o 1 (igual que las direcciones de move)."""
    return (value > 0) - (value < 0)


class World:
    def __init__(self, world_map=None, height=20, seed=None):
        """Crea un mundo.

        Acepta un WorldMap ya construido:

            World(map_def.build(), seed=7)

        y conserva la forma antigua para tests y CLI:

            World(10, 10, seed=7)

        En este último caso se crea un mapa vacío de 10x10 con el terreno
        por defecto.
        """
        if world_map is None:
            world_map = WorldMap.blank(40, height)
        elif isinstance(world_map, int):
            world_map = WorldMap.blank(world_map, height)

        self.map = world_map
        self.tick = 0
        self.creatures = []  # orden de creación = orden de turno
        self.roars = []  # [(tick, x, y, value), ...]
        self.log = []  # eventos: (tipo, tick, nombre, valor)
        self.interpreter = Interpreter()
        self.random = random.Random(seed)
        self._programs = {}  # id(SpeciesDef) -> Program (compartido)

    @property
    def width(self):
        return self.map.width

    @property
    def height(self):
        return self.map.height

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
            x,
            y,
        )
        if not self.map.place_creature(creature, x, y):
            raise ValueError(f"la casilla ({x}, {y}) no está libre")
        self.creatures.append(creature)
        return creature

    def add_object(self, object_type, x, y):
        """Coloca un objeto nuevo en (x, y). Pensado para tests y contenido."""
        obj = WorldObject(object_type)
        if not self.map.place_object(obj, x, y):
            raise ValueError(f"la casilla ({x}, {y}) no está libre")
        return obj

    def free_cells(self):
        """Casillas transitables sin objeto ni criatura."""
        return self.map.free_cells()

    def creature_at(self, x, y):
        """Criatura viva que ocupa (x, y), o None."""
        return self.map.creature_at(x, y)

    def kill(self, creature, reason):
        """Saca a la criatura del tablero y registra la muerte."""
        if not creature.alive:
            return
        self.map.remove_creature(creature)
        creature.kill(reason)
        self.log.append(("muerte", self.tick, creature.species, reason))

    # ------------------------------------------------------------------
    # Rondas
    # ------------------------------------------------------------------

    def run_round(self):
        """Una ronda: cada criatura viva hace su turno, en orden sorteado
        en cada tick

        Las crías nacidas durante la ronda no entran: su primer turno es
        el tick siguiente . Al cierre se aplican las leyes
        naturales y caducan los rugidos viejos.
        """
        order = [c for c in self.creatures if c.alive]
        self.random.shuffle(order)
        for creature in order:
            if not creature.alive:
                continue
            try:
                self.interpreter.run_turn(creature, self)
            except RuntimeFault as fault:
                self.kill(creature, f"ictus: {fault.message}")
        self._end_of_tick()
        return [c for c in self.creatures if c.alive]

    def _end_of_tick(self):
        """Leyes naturales al final de cada tick: toda criatura
        viva pierde 1 de vida y suma 1 de edad; muere quien llegue a 0 de
        vida o alcance su lifespan. Después el tablero regenera terrenos
        y retira los objetos agotados."""
        for creature in self.creatures:
            if not creature.alive:
                continue
            creature.health -= 1
            creature.age += 1
            if creature.health <= 0:
                creature.health = 0
                self.kill(creature, "hambre")
            elif creature.age >= creature.lifespan:
                self.kill(creature, "vejez")

        self.map.end_of_tick()
        self.tick += 1
        # El rugido del tick que acaba se oye durante el próximo (spec 2.6)
        self.roars = [r for r in self.roars if r[0] >= self.tick - 1]

    @staticmethod
    def _distance(x1, y1, x2, y2):
        """Chebyshev: el radio de visión es un cuadrado."""
        return max(abs(x1 - x2), abs(y1 - y2))

    def _distance_to(self, creature, x, y):
        return self._distance(creature.x, creature.y, x, y)

    def _nearby_creatures(self, creature):
        return [
            other
            for other in self.creatures
            if other.alive
            and other is not creature
            and self._distance_to(creature, other.x, other.y) <= creature.vision
        ]

    def _objects_in_vision(self, creature):
        """Objetos dentro del radio, recortando al tablero.

        El borde del mapa no es un objeto: si no hay casilla, no se cuenta.
        """
        vision = creature.vision
        x_start = max(0, creature.x - vision)
        x_end = min(self.map.width - 1, creature.x + vision)
        y_start = max(0, creature.y - vision)
        y_end = min(self.map.height - 1, creature.y + vision)

        return [
            (x, y)
            for y in range(y_start, y_end + 1)
            for x in range(x_start, x_end + 1)
            if self.map.object_at(x, y) is not None
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
        objects = self._objects_in_vision(creature)
        terrain = self.map.terrain_at(creature.x, creature.y)

        enemy_dist, enemy_dx, enemy_dy = self._nearest(
            creature, [(c.x, c.y) for c in enemies]
        )
        ally_dist, ally_dx, ally_dy = self._nearest(
            creature, [(c.x, c.y) for c in allies]
        )
        object_dist, object_dx, object_dy = self._nearest(creature, objects)

        heard = [
            r
            for r in self.roars
            if r[0] == self.tick - 1
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
            "terrain_here": terrain.name if terrain is not None else "",
            "reserve_here": terrain.reserve if terrain is not None else 0,
            # mundo
            "width": self.map.width,
            "height": self.map.height,
            "tick": self.tick,
            "total_creatures": sum(
                1 for c in self.creatures if c.alive and c is not creature
            ),
            "total_allies": sum(
                1
                for c in self.creatures
                if c.alive and c is not creature and c.faction == creature.faction
            ),
            "total_enemies": sum(
                1
                for c in self.creatures
                if c.alive and c is not creature and c.faction != creature.faction
            ),
            # cerca (radio de visión)
            "allies_near": len(allies),
            "enemies_near": len(enemies),
            "objects_near": len(objects),
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

        if name == "random":
            return self.random.randint(0, 99)
        return creature.perceptions.get(name, 0)

    # ------------------------------------------------------------------
    # Funciones reservadas (spec 2.6): coordenadas ABSOLUTAS
    # ------------------------------------------------------------------

    def see(self, creature, x, y):
        """NONE si no se ve; si no, ALLY/ENEMY > OBJECT > GROUND."""
        return self.map.see(creature, x, y)

    def name_at(self, creature, x, y):
        """Nombre de lo que hay en (x, y); '' si no se ve o no hay nada."""
        return self.map.name_at(creature, x, y)

    # ACTIONS

    def move(self, creature, dx, dy, speed):
        """Avanza hasta `speed` casillas; se para ante objeto, borde o bicho."""
        for _ in range(max(0, speed)):
            nx, ny = creature.x + dx, creature.y + dy
            if not self.map.is_walkable(nx, ny):
                break
            if not self.map.move_creature(creature, nx, ny):
                break

    def _hurt(self, creature, dx, dy, damage, kind):
        """Daña a quien haya en la casilla relativa. (0,0) golpea el
        terreno bajo la propia criatura.

        Prioridad: criatura > objeto > terreno. El objeto no desaparece en
        el acto: se retira al cerrar el tick, como pide la spec.
        """
        if dx == 0 and dy == 0:
            terrain = self.map.terrain_at(creature.x, creature.y)
            if terrain is not None:
                terrain.damage(damage)
            return

        cell = self.map.cell_at(creature.x + dx, creature.y + dy)
        if cell is None:
            return  # golpe al aire (violinazo)

        if cell.creature is not None:
            target = cell.creature
            target.health -= damage
            if target.health <= 0:
                target.health = 0
                self.kill(target, f"{kind} de {creature.species}")
        elif cell.obj is not None:
            cell.obj.damage(damage)
        else:
            cell.terrain.damage(damage)

    def attack(self, creature, dx, dy, damage):
        self._hurt(creature, dx, dy, damage, "ataque")

    def consume(self, creature, dx, dy, damage, heal):
        """Como attack y además el atacante gana `heal` de vida, básicamente se cura"""
        self._hurt(creature, dx, dy, damage, "consume")
        if not creature.alive:
            return
        creature.health += heal
        if creature.health <= 0:
            creature.health = 0
            self.kill(creature, "consume con cura no positiva")

    def reproduce(self, creature, dx, dy, health):
        """Cría en la casilla adyacente si la madre tiene vida de sobra:
        la madre gasta `health` puntos y la cría nace con
        exactamente esa vida, edad 0, sin variables y en 'start'."""
        nx, ny = creature.x + dx, creature.y + dy
        if not self.map.is_walkable(nx, ny):
            return  # aborto natural: no hay casilla
        if creature.health <= health:
            return  # aborto natural: sin vida de sobra
        child = self.add_creature(creature.species_def, nx, ny)
        child.health = health
        creature.health -= health
        if creature.health <= 0:
            creature.health = 0
            self.kill(creature, "parto")
        self.log.append(("nacimiento", self.tick, child.species, (nx, ny)))

    def roar(self, creature, value):
        """Registra el rugido: en el tick siguiente y lo oyen quienes estén
        en su radio de visión."""
        self.roars.append((self.tick, creature.x, creature.y, value))
        self.log.append(("rugido", self.tick, creature.species, value))

    def say(self, creature, value):
        """No toca el mundo: va al log (lo imprime la CLI)."""
        self.log.append(("dice", self.tick, creature.species, value))
