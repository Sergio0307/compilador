# Instinct — Dota 2

Simulador de un mundo de casillas con criaturas programables en el lenguaje
**Instinct**. El proyecto incluye:

- compilador e intérprete de `.ins` (léxico, sintaxis, semántica y errores de ejecución con línea);
- mundo simulado por ticks (terrenos, objetos, criaturas, regeneración y muerte);
- aplicación Pygame para elegir mapa, colocar criaturas, ejecutar y observar la partida;
- contenido temático de Dota 2: Grieta de los Ancestros, creeps Radiant/Dire y Roshan.

## Requisitos

- Python 3.14 (el entorno del repositorio usa 3.14.9)
- `pygame==2.6.1`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

Aplicación visual:

```bash
.venv/bin/python run_ui.py
```

Simulador de terminal:

```bash
.venv/bin/python main.py --map "Rift of the Ancients" --ticks 60 --seed 7
```

Archivos `.ins` concretos sobre un mapa en blanco:

```bash
.venv/bin/python main.py examples/annex/*.ins --ticks 5 --width 20 --height 12 --seed 7
```

Si no se indica `--map` ni archivos, se cargan todas las criaturas de
`creatures/` y el primer mapa disponible.

## Controles de la aplicación

| Acción | Control |
|---|---|
| Elegir mapa | `↑` / `↓` |
| Elegir especie | `←` / `→` |
| Colocar criatura | clic izquierdo en el mapa |
| Quitar criatura mal colocada | clic derecho |
| Empezar partida | botón `Empezar` |
| Pausar / seguir | `P` o botón `Pausa` / `Seguir` |
| Avanzar un tick | `Espacio` (deja la partida en pausa) |
| Velocidad 2 / 10 / 30 ticks/s | `1` / `2` / `3` o botones |
| Reiniciar (vuelve a preparación) | `R` o botón `Reiniciar` |
| Inspeccionar criatura | clic izquierdo durante la partida |
| Salir | `Esc` |

Durante la partida no se pueden colocar ni quitar criaturas. Al reiniciar se
conserva el mapa elegido, pero se crean terrenos, objetos y criaturas nuevos.

## Formato del contenido

```text
terrains/*.te     terrain Grass
                  char .
                  resource_max 100
                  regen 2

objects/*.ob      object Rock
                  char #
                  resource_max 100

maps/*.map        primera línea: nombre del mapa
                  siguientes líneas: filas del mismo largo

creatures/*.ins   cabecera + bloque start: (lenguaje Instinct)
```

Los caracteres de terreno y objeto deben ser únicos entre todos los archivos
cargados. En un mapa, un carácter de objeto se coloca sobre el primer terreno
declarado. Los errores de carga se informan con archivo y línea, y no impiden
cargar el resto del contenido.

## Arquitectura

```text
lang/       lexer, parser, AST, valores, semántica, acciones, intérprete
world/      Entity/Terrain/WorldObject/Creature, Cell, WorldMap, World
loaders/    carga y validación de .te, .ob, .map y .ins
ui/         ventana, mapa, inspector y log (Pygame)
main.py     simulación headless por terminal
examples/   ejemplos del anexo, listos para ejecutar
```

Decisiones importantes:

- `World` no depende de Pygame: la simulación completa corre desde terminal.
- `MapDef` es un plano inmutable; `build()` crea reservas nuevas en cada partida.
- Las acciones son subclases de `Action`; el intérprete no tiene una cadena de
  `if accion == "move"`.
- Las percepciones y constantes viven en `lang/catalog.py`; el analizador
  semántico y el intérprete las consultan como datos.
- `Entity` agrupa terreno, objeto y criatura; los tres comparten `reserve` y
  `damage()`, pero solo la criatura muere y solo el terreno se regenera.

## Pruebas

```bash
.venv/bin/python -m unittest tests.test_acceptance -v

.venv/bin/python -m lang.test_catalog
.venv/bin/python -m lang.test_compiler
.venv/bin/python -m lang.test_parser
.venv/bin/python -m lang.test_semantics
.venv/bin/python -m lang.test_interpreter
.venv/bin/python -m world.test_world

.venv/bin/python -m unittest \
  loaders.test_resource_manager loaders.test_map_loader \
  loaders.test_creature_loader loaders.test_baseline_content \
  loaders.test_dota_content world.test_entities world.test_map
```

La matriz de aceptación y las comprobaciones manuales están en
[docs/acceptance.md](docs/acceptance.md).

## Ejemplos del anexo

`examples/annex/` contiene `uruk.ins`, `hobbit.ins`, `ent.ins` y `dwarf.ins`
sin modificar. No se cargan automáticamente en la aplicación para no mezclar
los ejemplos del profesor con el contenido de Dota; se pueden ejecutar con
`main.py` o copiar a `creatures/` si se quieren ver en el selector.

## Limitaciones conocidas

- No hay guardado/carga de partidas, gráficas de población ni editor de mapas.
- La interfaz dibuja formas geométricas; los sprites/animaciones son una
  extensión opcional.
- `not` comparte precedencia con el menos unario, como indica la especificación
  (no exactamente como Python).
