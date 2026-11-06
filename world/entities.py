"""Definiciones compartidas de terrenos y objetos.

Estas clases describen qué es un terreno o un objeto según los archivos
`.te` y `.ob`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TerrainType:
    """Definición inmutable de un terreno cargado desde un archivo `.te`."""

    name: str
    char: str
    resource_max: int
    regen: int


@dataclass(frozen=True)
class ObjectType:
    """Definición inmutable de un objeto cargado desde un archivo `.ob`."""

    name: str
    char: str
    resource_max: int


class Entity(ABC):
    """Algo que ocupa una casilla y puede recibir daño.

    Terrain, WorldObject y Creature comparten esto. Así se puede atacar una casilla sin preguntar de qué
    tipo es.

    name y char describen cómo se muestra, reserve es lo que queda
    antes de que el objeto desaparezca o el terreno se agote.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def char(self) -> str:
        pass

    @property
    @abstractmethod
    def reserve(self) -> int:
        pass

    @abstractmethod
    def damage(self, amount: int) -> bool:
        """Resta amount a la reserva y devuelve True si quedó destruido."""


class Terrain(Entity):
    """Una casilla de terreno con su propia reserva.

    La definición TerrainType se comparte entre todas las casillas del
    mismo tipo, la reserva es individual y se gasta al atacar o consumir.
    """

    def __init__(self, terrain_type: TerrainType):
        self.type = terrain_type
        self._reserve = terrain_type.resource_max

    @property
    def name(self) -> str:
        return self.type.name

    @property
    def char(self) -> str:
        return self.type.char

    @property
    def reserve(self) -> int:
        return self._reserve

    @property
    def resource_max(self) -> int:
        return self.type.resource_max

    def damage(self, amount: int) -> bool:
        """Gasta reserva, el terreno nunca desaparece, solo llega a cero."""
        self._reserve = min(self.resource_max, max(0, self._reserve - amount))
        return False

    def regenerate(self) -> None:
        """Recupera `regen` por tick, sin pasar de resource_max."""
        self._reserve = min(self.resource_max, self._reserve + self.type.regen)


class WorldObject(Entity):
    """Un objeto de una casilla: no regenera y desaparece al llegar a cero."""

    def __init__(self, object_type: ObjectType):
        self.type = object_type
        self._reserve = object_type.resource_max

    @property
    def name(self) -> str:
        return self.type.name

    @property
    def char(self) -> str:
        return self.type.char

    @property
    def reserve(self) -> int:
        return self._reserve

    @property
    def resource_max(self) -> int:
        return self.type.resource_max

    def damage(self, amount: int) -> bool:
        """Gasta reserva, devuelve True cuando el objeto queda destruido."""
        self._reserve = min(self.resource_max, max(0, self._reserve - amount))
        return self._reserve <= 0
