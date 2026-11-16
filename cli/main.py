"""CLI de Instinct: compila archivos .ins, simula el mundo y muestra el resultado.

    python main.py criatura1.ins criatura2.ins [--ticks 100] [--width 40]
                    [--height 20] [--seed 7]

Una criatura por archivo, nacida en una casilla libre aleatoria. Imprime
los eventos (say, rugidos, muertes, nacimientos) ronda a ronda y un
resumen final. Corta en --ticks o cuando no queda nadie viva.
"""

import argparse
import sys

from lang.compiler import compile_species
from lang.errors import InstinctError
from world.world import World


EVENT_WORDS = {
    "dice":       lambda nombre, valor: f"{nombre} dice: {valor}",
    "rugido":     lambda nombre, valor: f"{nombre} ruge: {valor}",
    "muerte":     lambda nombre, valor: f"{nombre} muere ({valor})",
    "nacimiento": lambda nombre, valor: f"{nombre} nace en {valor}",
}


def cargar(path):
    """Lee y compila un .ins; devuelve el SpeciesDef o aborta con error."""
    try:
        with open(path, encoding="utf-8") as fh:
            return compile_species(fh.read(), path)
    except OSError as error:
        print(f"error: no se pudo leer {path}: {error}", file=sys.stderr)
        raise SystemExit(1)
    except InstinctError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:  # 4.3: Red de seguridad para bugs internos
        print(f"error interno en {path}: {error}", file=sys.stderr)
        raise SystemExit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Simulador de especies Instinct (.ins)")
    parser.add_argument("files", nargs="+", metavar="archivo.ins",
                        help="especies que participan en la simulación")
    parser.add_argument("--ticks", type=int, default=100,
                        help="máximo de rondas a simular (100)")
    parser.add_argument("--width", type=int, default=40, help="ancho del mapa")
    parser.add_argument("--height", type=int, default=20, help="alto del mapa")
    parser.add_argument("--seed", type=int, default=None,
                        help="semilla del RNG para reproducción exacta")
    args = parser.parse_args(argv)

    # 4.2: Validar argumentos CLI - deben ser >= 1
    if args.ticks < 1:
        print(f"error: --ticks debe ser >= 1 (se recibió {args.ticks})", file=sys.stderr)
        raise SystemExit(1)
    if args.width < 1:
        print(f"error: --width debe ser >= 1 (se recibió {args.width})", file=sys.stderr)
        raise SystemExit(1)
    if args.height < 1:
        print(f"error: --height debe ser >= 1 (se recibió {args.height})", file=sys.stderr)
        raise SystemExit(1)

    # Compila TODO antes de simular: un .ins roto corta aquí, sin gastar rondas
    species = [(path, cargar(path)) for path in args.files]

    world = World(args.width, args.height, seed=args.seed)

    # 4.4: Calcular celdas libres una vez y actualizar incrementalmente
    free_cells = set(world.free_cells())

    for path, sp in species:
        if not free_cells:
            print("error: no hay casillas libres para nacer", file=sys.stderr)
            raise SystemExit(1)
        x, y = free_cells.pop()  # Elige y elimina de una vez
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
        print(f"  {c.species} ({c.faction}) hp {c.health}/{c.max_health} "
              f"edad {c.age}/{c.lifespan} en ({c.x}, {c.y})")
    for c in world.creatures:
        if not c.alive:
            print(f"  {c.species} murió: {c.death_reason}")
    raise SystemExit(0)


if __name__ == "__main__":
    sys.exit(main())
