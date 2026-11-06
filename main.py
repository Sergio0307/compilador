"""CLI de Instinct: compila archivos .ins, simula el mundo y muestra el resultado.

    python main.py [criatura1.ins ...] [--map "Test Field"] [--ticks 100]
                    [--content .] [--seed 7]

Sin archivos .ins usa todas las especies cargadas de creatures/. Si se
indica --map, simula sobre ese mapa. Si hay archivos explícitos y no se
indica --map, usa un mapa en blanco de --width x --height. Si no hay
archivos ni --map, usa el primer mapa cargado. Imprime los eventos (say,
rugidos, muertes, nacimientos) ronda a ronda y un resumen final. Corta en
--ticks o cuando no queda nadie vivo.
"""

import argparse
import sys

from lang.compiler import compile_species
from lang.errors import InstinctError
from loaders.resource_manager import ResourceManager
from world.world import World

EVENT_WORDS = {
    "dice": lambda nombre, valor: f"{nombre} dice: {valor}",
    "rugido": lambda nombre, valor: f"{nombre} ruge: {valor}",
    "muerte": lambda nombre, valor: f"{nombre} muere ({valor})",
    "nacimiento": lambda nombre, valor: f"{nombre} nace en {valor}",
}


def cargar(path):
    """Lee y compila un .ins, devuelve el SpeciesDef o aborta con error."""
    try:
        with open(path, encoding="utf-8") as f:
            return compile_species(f.read(), path)
    except OSError as error:
        print(f"error: no se pudo leer {path}: {error}", file=sys.stderr)
        raise SystemExit(1)
    except InstinctError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)


def entero_positivo(texto):
    """argparse: entero >= 1, para --width y --height."""
    try:
        valor = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' no es un entero")
    if valor < 1:
        raise argparse.ArgumentTypeError("debe ser mayor que 0")
    return valor


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Simulador de especies Instinct (.ins)"
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="archivo.ins",
        help="especies que participan, si se omiten, se usan las de creatures/",
    )
    parser.add_argument(
        "--ticks", type=int, default=100, help="máximo de rondas a simular (100)"
    )
    parser.add_argument(
        "--content",
        default=".",
        help="raíz con terrains/, objects/, maps/ y creatures/ (.)",
    )
    parser.add_argument(
        "--map",
        dest="map_name",
        default=None,
        help="nombre del mapa; si se omite y no hay archivos, usa el primero",
    )
    parser.add_argument(
        "--width",
        type=entero_positivo,
        default=40,
        help="ancho del mapa en blanco (40)",
    )
    parser.add_argument(
        "--height",
        type=entero_positivo,
        default=20,
        help="alto del mapa en blanco (20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="semilla del RNG para reproducción exacta",
    )
    args = parser.parse_args(argv)

    manager = None
    if args.map_name or not args.files:
        manager = ResourceManager(args.content)
        manager.load_all()
        for error in manager.errors:
            print(f"aviso: {error}", file=sys.stderr)

    # Compila todo antes de simular: un .ins roto corta aquí, sin gastar rondas
    if args.files:
        species = [(path, cargar(path)) for path in args.files]
    else:
        if manager is None:
            print("error: no se pudo cargar el contenido", file=sys.stderr)
            return 1
        if not manager.creatures:
            print("error: no hay especies en creatures/", file=sys.stderr)
            return 1
        species = [
            (f"contenido/{name}.ins", sp) for name, sp in manager.creatures.items()
        ]

    map_def = None
    if args.map_name:
        if manager is None:
            print("error: no se pudo cargar el contenido", file=sys.stderr)
            return 1
        map_def = manager.maps.get(args.map_name)
        if map_def is None:
            disponibles = ", ".join(manager.maps) or "(ninguno)"
            print(
                f"error: no existe el mapa '{args.map_name}', "
                f"disponibles: {disponibles}",
                file=sys.stderr,
            )
            return 1
    elif manager is not None and not args.files and manager.maps:
        map_def = next(iter(manager.maps.values()))

    if map_def is not None:
        world = World(map_def.build(), seed=args.seed)
        print(f"mapa: {map_def.name} ({map_def.width}x{map_def.height})")
    else:
        world = World(args.width, args.height, seed=args.seed)

    for path, sp in species:
        cells = world.free_cells()
        if not cells:
            print("error: no hay casillas libres para nacer", file=sys.stderr)
            return 1
        x, y = cells[world.random.randrange(len(cells))]
        world.add_creature(sp, x, y)
        print(f"{path}: {sp.name} ({sp.faction}) nace en ({x}, {y})")

    mostrados = 0
    while world.tick < args.ticks and any(c.alive for c in world.creatures):
        world.run_round()
        for kind, tick, nombre, valor in world.log[mostrados:]:
            print(f"  [t{tick}] " + EVENT_WORDS[kind](nombre, valor))
        mostrados = len(world.log)

    vivos = [c for c in world.creatures if c.alive]
    print(f"\n=== fin en tick {world.tick}: {len(vivos)} vivas ===")
    for c in vivos:
        print(
            f"  {c.species} ({c.faction}) hp {c.health} "
            f"(inicial {c.max_health}) edad {c.age}/{c.lifespan} "
            f"en ({c.x}, {c.y})"
        )
    for c in world.creatures:
        if not c.alive:
            print(f"  {c.species} murió: {c.death_reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
