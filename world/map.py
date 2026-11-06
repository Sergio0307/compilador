from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lang.catalog import CONSTANTS
from world.entities import ObjectType, Terrain, TerrainType, WorldObject

if TYPE_CHECKING:
    from world.creature import Creature


DEFAULT_TERRAIN = TerrainType("Grass", ".", 100, 2)


@dataclass
class Cell:
    """Una casilla: terreno fijo, más un objeto o una criatura como máximo."""

    terrain: Terrain
    obj: WorldObject | None = None
    creature: Creature | None = None

    def __post_init__(self):
        if self.obj is not None and self.creature is not None:
            raise ValueError("una casilla no puede tener objeto y criatura a la vez")

    @property
    def is_free(self) -> bool:
        return self.obj is None and self.creature is None


class WorldMap:
    """Matriz de casillas."""

    def __init__(self, name: str, grid: list[list[Cell]]):
        if not grid or not grid[0]:
            raise ValueError("el mapa no puede estar vacío")

        self.name = name
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0])

        if any(len(row) != self.width for row in grid):
            raise ValueError("todas las filas deben tener el mismo ancho")

    @classmethod
    def blank(
        cls,
        width: int,
        height: int,
        terrain_type: TerrainType | None = None,
    ) -> WorldMap:
        """Crea un mapa rectangular sin objetos ni criaturas."""
        if width <= 0 or height <= 0:
            raise ValueError("el ancho y el alto deben ser positivos")

        terrain_type = terrain_type or DEFAULT_TERRAIN
        grid = [
            [Cell(Terrain(terrain_type)) for _ in range(width)] for _ in range(height)
        ]
        return cls("Blank", grid)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell_at(self, x: int, y: int) -> Cell | None:
        if not self.in_bounds(x, y):
            return None
        return self.grid[y][x]

    def terrain_at(self, x: int, y: int) -> Terrain | None:
        cell = self.cell_at(x, y)
        return None if cell is None else cell.terrain

    def object_at(self, x: int, y: int) -> WorldObject | None:
        cell = self.cell_at(x, y)
        return None if cell is None else cell.obj

    def creature_at(self, x: int, y: int) -> Creature | None:
        cell = self.cell_at(x, y)
        return None if cell is None else cell.creature

    def is_walkable(self, x: int, y: int) -> bool:
        """Se puede pisar si está dentro y no hay objeto ni criatura."""
        cell = self.cell_at(x, y)
        return cell is not None and cell.is_free

    @staticmethod
    def _distance(viewer: Creature, x: int, y: int) -> int:
        """Distancia de vista: el radio de visión es cuadrado."""
        return max(abs(viewer.x - x), abs(viewer.y - y))

    def see(self, viewer: Creature, x: int, y: int) -> int:
        """Valor de see(x, y) para viewer

        El orden importa:
        1. fuera del radio de visión -> NONE;
        2. la propia casilla -> ALLY;
        3. fuera del mapa pero dentro de visión -> OBJECT (borde);
        4. criatura -> ALLY/ENEMY según facción;
        5. objeto -> OBJECT;
        6. terreno solo -> GROUND.
        """
        if self._distance(viewer, x, y) > viewer.vision:
            return CONSTANTS["NONE"]

        if viewer.x == x and viewer.y == y:
            return CONSTANTS["ALLY"]

        cell = self.cell_at(x, y)
        if cell is None:
            return CONSTANTS["OBJECT"]

        if cell.creature is not None:
            if cell.creature.faction == viewer.faction:
                return CONSTANTS["ALLY"]
            return CONSTANTS["ENEMY"]

        if cell.obj is not None:
            return CONSTANTS["OBJECT"]

        return CONSTANTS["GROUND"]

    def name_at(self, viewer: Creature, x: int, y: int) -> str:
        """Valor de name(x, y) para viewer

        Devuelve el nombre de la especie si hay criatura, el nombre del
        objeto si hay objeto, o el nombre del terreno si la casilla está
        vacía. Fuera de visión o fuera del mapa devuelve: ("").
        """
        if self._distance(viewer, x, y) > viewer.vision:
            return ""

        cell = self.cell_at(x, y)
        if cell is None:
            return ""

        if cell.creature is not None:
            return cell.creature.species
        if cell.obj is not None:
            return cell.obj.name
        return cell.terrain.name

    def free_cells(self) -> list[tuple[int, int]]:
        return [
            (x, y)
            for y, row in enumerate(self.grid)
            for x, cell in enumerate(row)
            if cell.is_free
        ]

    def end_of_tick(self) -> None:
        """Regenera todos los terrenos y retira objetos agotados.

        El orden sigue la spec: primero se regenera el terreno de cada
        casilla y después desaparecen los objetos con reserva <= 0.
        """
        for row in self.grid:
            for cell in row:
                cell.terrain.regenerate()
                if cell.obj is not None and cell.obj.reserve <= 0:
                    cell.obj = None

    def place_creature(self, creature: Creature, x: int, y: int) -> bool:
        """Coloca una criatura y actualiza sus coordenadas, False si no cabe."""
        cell = self.cell_at(x, y)
        if cell is None or not cell.is_free:
            return False

        cell.creature = creature
        creature.x = x
        creature.y = y
        return True

    def place_object(self, obj: WorldObject, x: int, y: int) -> bool:
        cell = self.cell_at(x, y)
        if cell is None or not cell.is_free:
            return False

        cell.obj = obj
        return True

    def remove_creature(self, creature: Creature) -> bool:
        cell = self.cell_at(creature.x, creature.y)
        if cell is None or cell.creature is not creature:
            return False

        cell.creature = None
        return True

    def move_creature(self, creature: Creature, x: int, y: int) -> bool:
        """Mueve a la casilla destino, False si está ocupada o fuera."""
        origin = self.cell_at(creature.x, creature.y)
        if origin is None or origin.creature is not creature:
            return False

        target = self.cell_at(x, y)
        if target is None or not target.is_free:
            return False

        origin.creature = None
        target.creature = creature
        creature.x = x
        creature.y = y
        return True


@dataclass(frozen=True)
class TileSpec:
    """Propiedades de una casilla."""

    terrain: TerrainType
    obj: ObjectType | None = None


@dataclass(frozen=True)
class MapDef:
    """Plano inmutable de un mapa cargado desde un archivo .map.

    Guarda definiciones (TerrainType/ObjectType), no casillas vivas. Cada
    llamada a build() crea terrenos y objetos nuevos, con sus reservas
    completas. Así se puede reiniciar una partida sin arrastrar el estado
    de la anterior.
    """

    name: str
    tiles: tuple[tuple[TileSpec, ...], ...]

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("el nombre del mapa no puede estar vacío")
        if not self.tiles:
            raise ValueError("el mapa no puede estar vacío")

        width = len(self.tiles[0])
        if width == 0:
            raise ValueError("las filas del mapa no pueden estar vacías")
        if any(len(row) != width for row in self.tiles):
            raise ValueError("todas las filas deben tener el mismo ancho")

    @property
    def width(self) -> int:
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        return len(self.tiles)

    def build(self) -> WorldMap:
        """Crea un WorldMap nuevo a partir del plano."""
        grid = []
        for row in self.tiles:
            cells = []
            for tile in row:
                obj = None if tile.obj is None else WorldObject(tile.obj)
                cells.append(Cell(Terrain(tile.terrain), obj=obj))
            grid.append(cells)
        return WorldMap(self.name, grid)
