"""Carga del contenido del juego: terrenos, objetos, mapas y criaturas.

Los archivos `.te`, `.ob` y `.map` son texto de configuración; los `.ins`
se compilan con el pipeline del lenguaje. El cargador no lanza excepciones
por un archivo malo: acumula `LoadError` con archivo y línea, ignora ese
archivo y sigue con los demás. Así la aplicación puede abrir un proyecto
con contenido parcial sin cerrarse.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lang.compiler import compile_species
from lang.errors import InstinctError, SemanticErrors
from world.entities import ObjectType, TerrainType
from world.map import MapDef, TileSpec


@dataclass(frozen=True)
class LoadError:
    path: str
    line: int | None
    message: str

    def __str__(self) -> str:
        if self.line is None:
            return f"{self.path}: {self.message}"
        return f"{self.path}:{self.line}: {self.message}"


class ResourceManager:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self.terrains: dict[str, TerrainType] = {}
        self.objects: dict[str, ObjectType] = {}
        self.maps = {}
        self.creatures = {}
        self.errors: list[LoadError] = []

    def load_all(self):
        """Carga todo en orden: terrenos, objetos, mapas y criaturas."""
        self.errors.clear()
        self.terrains = {}
        self.objects = {}
        self.maps = {}
        self.creatures = {}

        self.terrains = self.load_terrains()
        self.objects = self.load_objects()
        self.maps = self.load_maps()
        self.creatures = self.load_creatures()
        return self.errors

    def load_terrains(self) -> dict[str, TerrainType]:
        terrains: dict[str, TerrainType] = {}
        used_chars = {obj.char: obj.name for obj in self.objects.values()}
        allowed = {"terrain", "char", "resource_max", "regen"}

        for path in self._files("terrains", ".te"):
            lines = self._read(path)
            if lines is None:
                continue

            fields, valid = self._fields(path, lines, allowed)
            if not valid:
                continue

            missing = [key for key in allowed if key not in fields]
            if missing:
                self._error(path, None, "faltan claves: " + ", ".join(sorted(missing)))
                continue

            name, name_line = fields["terrain"]
            if not name:
                self._error(
                    path, name_line, "el nombre del terreno no puede estar vacío"
                )
                continue

            char, char_line = fields["char"]
            if len(char) != 1:
                self._error(path, char_line, "el carácter debe ser exactamente uno")
                continue

            resource_max = self._int(path, fields, "resource_max")
            regen = self._int(path, fields, "regen")
            if resource_max is None or regen is None:
                continue

            if char in used_chars:
                self._error(
                    path,
                    char_line,
                    f"carácter '{char}' ya usado por '{used_chars[char]}'",
                )
                continue

            if name in terrains:
                self._error(path, name_line, f"terreno duplicado '{name}'")
                continue

            terrains[name] = TerrainType(name, char, resource_max, regen)
            used_chars[char] = name

        return terrains

    def load_objects(self) -> dict[str, ObjectType]:
        objects: dict[str, ObjectType] = {}
        used_chars = {terrain.char: terrain.name for terrain in self.terrains.values()}
        allowed = {"object", "char", "resource_max"}

        for path in self._files("objects", ".ob"):
            lines = self._read(path)
            if lines is None:
                continue

            fields, valid = self._fields(path, lines, allowed)
            if not valid:
                continue

            missing = [key for key in allowed if key not in fields]
            if missing:
                self._error(path, None, "faltan claves: " + ", ".join(sorted(missing)))
                continue

            name, name_line = fields["object"]
            if not name:
                self._error(
                    path, name_line, "el nombre del objeto no puede estar vacío"
                )
                continue

            char, char_line = fields["char"]
            if len(char) != 1:
                self._error(path, char_line, "el carácter debe ser exactamente uno")
                continue

            resource_max = self._int(path, fields, "resource_max")
            if resource_max is None:
                continue

            if char in used_chars:
                self._error(
                    path,
                    char_line,
                    f"carácter '{char}' ya usado por '{used_chars[char]}'",
                )
                continue

            if name in objects:
                self._error(path, name_line, f"objeto duplicado '{name}'")
                continue

            objects[name] = ObjectType(name, char, resource_max)
            used_chars[char] = name

        return objects

    def load_maps(self) -> dict[str, MapDef]:
        maps: dict[str, MapDef] = {}
        terrain_by_char = {terrain.char: terrain for terrain in self.terrains.values()}
        object_by_char = {obj.char: obj for obj in self.objects.values()}
        first_terrain = next(iter(self.terrains.values()), None)

        for path in self._files("maps", ".map"):
            lines = self._read(path)
            if lines is None:
                continue
            if not lines:
                self._error(path, None, "el mapa está vacío")
                continue

            name = lines[0].strip()
            if not name:
                self._error(path, 1, "el nombre del mapa no puede estar vacío")
                continue

            if name in maps:
                self._error(path, 1, f"mapa duplicado '{name}'")
                continue

            rows = lines[1:]
            if not rows:
                self._error(path, None, "el mapa no tiene filas")
                continue

            width = len(rows[0])
            if width == 0:
                self._error(path, 2, "la primera fila está vacía")
                continue

            invalid = False
            for offset, row in enumerate(rows):
                if len(row) != width:
                    self._error(
                        path,
                        offset + 2,
                        f"la fila mide {len(row)}, se esperaba {width}",
                    )
                    invalid = True
                    break
            if invalid:
                continue

            tile_rows: list[tuple[TileSpec, ...]] = []
            for offset, row in enumerate(rows):
                line_number = offset + 2
                tiles: list[TileSpec] = []
                for char in row:
                    if char in terrain_by_char:
                        tiles.append(TileSpec(terrain_by_char[char]))
                        continue

                    obj = object_by_char.get(char)
                    if obj is not None:
                        if first_terrain is None:
                            self._error(
                                path,
                                line_number,
                                f"no hay terreno para colocar el objeto '{obj.name}'",
                            )
                            invalid = True
                            break
                        tiles.append(TileSpec(first_terrain, obj))
                        continue

                    self._error(
                        path,
                        line_number,
                        f"carácter desconocido '{char}'",
                    )
                    invalid = True
                    break

                if invalid:
                    break
                tile_rows.append(tuple(tiles))

            if invalid:
                continue

            try:
                maps[name] = MapDef(name, tuple(tile_rows))
            except ValueError as exc:
                self._error(path, None, str(exc))

        return maps

    def load_creatures(self) -> dict:
        creatures = {}

        for path in self._files("creatures", ".ins"):
            lines = self._read(path)
            if lines is None:
                continue

            source = "\n".join(lines)
            try:
                species = compile_species(source, str(path))
            except SemanticErrors as e:
                for error in e.errors:
                    self._error(path, error.line, error.message)
                continue
            except InstinctError as e:
                self._error(path, e.line, e.message)
                continue

            if species.name in creatures:
                self._error(
                    path,
                    species.line or 1,
                    f"especie duplicada '{species.name}'",
                )
                continue

            creatures[species.name] = species

        return creatures

    def _files(self, directory: str, suffix: str) -> list[Path]:
        base = self.root / directory
        if not base.is_dir():
            self._error(base, None, "no existe el directorio")
            return []
        return sorted(base.glob(f"*{suffix}"))

    def _read(self, path: Path) -> list[str] | None:
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as e:
            self._error(path, None, f"no se pudo leer: {e}")
            return None

    def _fields(
        self,
        path: Path,
        lines: list[str],
        allowed: set[str],
    ) -> tuple[dict[str, tuple[str, int]], bool]:
        """Devuelve los campos y si el archivo es válido."""
        fields: dict[str, tuple[str, int]] = {}
        valid = True

        for number, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)
            if len(parts) != 2:
                self._error(path, number, "se esperaba 'clave valor'")
                valid = False
                continue

            key, value = parts
            if key not in allowed:
                self._error(path, number, f"clave desconocida '{key}'")
                valid = False
                continue

            if key in fields:
                self._error(path, number, f"clave duplicada '{key}'")
                valid = False
                continue

            fields[key] = (value.strip(), number)

        return fields, valid

    def _int(
        self,
        path: Path,
        fields: dict[str, tuple[str, int]],
        key: str,
    ) -> int | None:
        raw, line = fields[key]
        try:
            value = int(raw)
        except ValueError:
            self._error(path, line, f"'{key}' debe ser un entero")
            return None

        if value < 0:
            self._error(path, line, f"'{key}' no puede ser negativo")
            return None

        return value

    def _error(self, path: str | Path, line: int | None, message: str) -> None:
        self.errors.append(LoadError(str(path), line, message))
