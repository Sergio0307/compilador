# Matriz de aceptación

Base de referencia: `instinct.pdf`, secciones 2–5 y anexos.
Estado: **base funcional completa**. Las extensiones visuales (inspector,
barras de vida, contenido Dota) no sustituyen ninguna regla base.

## Comandos

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

## 2. Lenguaje Instinct

| Requisito | Evidencia | Estado |
|---|---|---|
| Cabecera con 5 claves y `creature` primero | `lang.test_parser`, `lang.test_semantics` | OK |
| Comentarios, etiquetas, `goto`, `if`, asignación, acciones | `lang.test_parser`, `lang.test_interpreter` | OK |
| 7 acciones y su aridad | `lang.test_catalog`, `lang.test_interpreter` | OK |
| `wait(n)` salta turnos y `say` no consume turno | `lang.test_interpreter` | OK |
| `move`/`attack`/`consume`/`reproduce` y direcciones | `world.test_world` | OK |
| Expresiones, tipos y precedencia | `lang.test_parser`, `lang.test_interpreter` | OK |
| `not` al mismo nivel que el menos unario | `lang.test_parser` | OK |
| `see()`/`name()` y límites del mapa | `world.test_map` | OK |
| Percepciones propias, del mundo y cercanas | `lang.test_catalog`, `world.test_world` | OK |
| Orden de turno aleatorio, `pc` guardado, 100 líneas | `lang.test_interpreter` | OK |
| Errores de compilación con línea | `lang.test_semantics`, `lang.test_compiler` | OK |
| Errores de ejecución con línea y muerte | `lang.test_interpreter`, `world.test_world` | OK |
| Ejemplos del anexo compilan y corren sin cambios | `tests.test_acceptance` | OK |

## 3. Mundo

| Requisito | Evidencia | Estado |
|---|---|---|
| Celda = terreno + objeto **o** criatura | `world.test_map` | OK |
| Terreno transitable, reserva llena y regeneración | `world.test_entities`, `world.test_world` | OK |
| Objeto no transitable, sin regeneración y desaparece | `world.test_entities`, `world.test_world` | OK |
| Criatura no transitable; reserva = vida | `world.test_world` | OK |
| `attack`/`consume` dañan criatura, objeto o terreno | `world.test_world` | OK |
| `(0,0)` golpea el terreno bajo la criatura | `world.test_world` | OK |
| Mapa: nombre, filas rectangulares, caracteres únicos | `loaders.test_map_loader` | OK |
| Objeto de mapa sobre el primer terreno declarado | `loaders.test_map_loader` | OK |
| Carácter desconocido rechaza solo ese mapa | `loaders.test_map_loader` | OK |
| Fin de tick: vida/edad, muertes, regeneración, objetos | `world.test_world` | OK |
| `total_creatures` excluye a la propia criatura | `world.test_world` | OK |
| `objects_near` no cuenta el borde del mapa | `world.test_world` | OK |
| Carga `.te → .ob → .map → .ins` y errores con línea | `loaders.test_resource_manager`, `loaders.test_creature_loader` | OK |

## 4. Aplicación

| Requisito | Evidencia | Estado |
|---|---|---|
| Carga contenido del repo al arrancar | `tests.test_acceptance` | OK |
| Elegir mapa | UI, `↑`/`↓` | OK |
| Colocar varias criaturas de la misma especie | UI, clic izquierdo | OK |
| Quitar criatura mal colocada | UI, clic derecho | OK |
| No colocar sobre objeto ni criatura | UI, `ValueError` controlado | OK |
| Pausa, un tick y 3 velocidades | UI, `P`/`Espacio`/`1-3` | OK |
| No editar durante la partida | UI, guardas de fase | OK |
| Reiniciar vuelve a preparación | UI, `R` | OK |
| Log de carga, ejecución y eventos | UI, panel `Registro` | OK |
| Errores de carga visibles durante la partida | UI, `Registro · carga: N` | OK |
| Errores de ejecución con línea | `world.test_world` | OK |
| Dibujar terrenos/objetos desconocidos con fallback | `ui/map.py` | OK |

## 5. Diseño

| Requisito | Evidencia | Estado |
|---|---|---|
| `Action` abstracta + subclase por acción | `lang/actions.py` | OK |
| AST que se evalúa a sí mismo | `lang/ast_nodes.py` | OK |
| Jerarquía `Entity`/`Terrain`/`WorldObject`/`Creature` | `world/entities.py`, `world/creature.py` | OK |
| Percepciones por catálogo, sin cadena de ifs | `lang/catalog.py` | OK |
| Mundo separado de la interfaz; simulación headless | `main.py`, `World` | OK |
| Intérprete como recorrido de AST | `lang/interpreter.py` | OK |
| App mínima: mapa, criaturas, log, tiempo | `ui/app.py` | OK |
| Extensiones no reemplazan la base | inspector/barras/contenido | OK |

## Comprobación manual de la app

1. `run_ui.py` abre en preparación; `↑`/`↓` cambia de mapa y el panel derecho se redibuja.
2. `←`/`→` cambia de especie; clic izquierdo coloca; clic derecho quita.
3. `Empezar` sin criaturas muestra el aviso y no inicia.
4. Con una criatura, `Empezar` inicia; `Espacio` avanza un tick y deja pausa; `P` alterna pausa.
5. `1`/`2`/`3` cambian la velocidad; el acumulador no arrastra ticks viejos.
6. `R` vuelve a preparación con tick 0, sin criaturas y velocidad 2.
7. Clic en una criatura durante la partida abre el inspector; al morir o reiniciar se limpia.
8. Un archivo inválido en `terrains/` muestra `aviso:` y `Registro · carga: N`; el resto carga.
9. Una especie que divide por cero muere con `(línea N)` en el registro.

## Limitaciones conocidas

- Sin guardado/carga, gráficas de población, editor de mapas ni sprites.
- El inspector muestra hasta 3 variables y tres percepciones resumidas.
- Los ejemplos del anexo viven en `examples/annex/` y no se cargan en el selector
  por defecto; se ejecutan con `main.py` o se copian a `creatures/`.
