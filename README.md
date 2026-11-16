# Instinct — Simulador de Criaturas

> Un compilador e intérprete para el lenguaje **Instinct (`.ins`)** + motor de simulación de criaturas en un mundo 2D.

---

## 📋 Descripción

**Instinct** es un lenguaje de programación minimalista diseñado para definir el comportamiento de criaturas autónomas que viven en un mundo simulado. Cada criatura ejecuta su propio programa (archivo `.ins`) turno a turno, percibe su entorno, toma decisiones y actúa.

El proyecto incluye:

- **Compilador** completo: léxico → sintáctico → semántico → intérprete
- **Motor de simulación**: mundo 2D, criaturas, percepciones, acciones, combate, reproducción
- **CLI** para ejecutar simulaciones desde terminal

---

## 🚀 Instalación

```bash
git clone https://github.com/Sergio0307/compilador.git
cd compilador
# No requiere dependencias externas (solo Python 3.10+)
```

---

## 🎮 Uso Rápido

### 1. Crear un archivo `.ins`

```instinct
creature Uruk
faction isengard
health 80
vision 6
lifespan 400

start:
if health < 20 goto flee
goto start

flee:
move(-enemy_dx, -enemy_dy, 3)
goto start
```

### 2. Ejecutar la simulación

```bash
# Una especie
python main.py uruk.ins

# Varias especies compitiendo
python main.py uruk.ins orc.ins --ticks 200 --width 60 --height 30 --seed 42
```

### 3. Argumentos CLI

| Argumento | Descripción | Default |
|-----------|-------------|---------|
| `archivo.ins` | Especies a simular (1+) | **requerido** |
| `--ticks N` | Máximo de rondas | `100` |
| `--width N` | Ancho del mapa | `40` |
| `--height N` | Alto del mapa | `20` |
| `--seed N` | Semilla RNG (reproducible) | `aleatorio` |

---

## 📝 Sintaxis del Lenguaje `.ins`

### Cabecera (obligatoria, 5 claves)

```instinct
creature NombreEspecie    # nombre (letras, dígitos, _)
faction nombre_faccion    # facción (agrupa aliados/enemigos)
health 80                 # vida inicial > 0
vision 6                  # radio de visión ≥ 1
lifespan 400              # edad máxima > 0
```

### Cuerpo: etiquetas + instrucciones

```instinct
etiqueta:                 # define un punto de salto
goto etiqueta             # salto incondicional
if condicion goto etiqueta # salto condicional
variable = expresion      # asignación (solo variables propias)
accion(arg1, arg2, ...)   # acción que consume turno
say("texto")              # mensaje (NO consume turno)
```

### Expresiones

- **Literales**: `42`, `"texto"`, `true`/`false` (1/0)
- **Variables**: `health`, `enemy_dx`, `random`, etc.
- **Funciones**: `see(x, y)`, `name(x, y)`
- **Operadores** (precedencia Python-style):
  - `or` < `and` < `not` < `== != < <= > >=` < `+ -` < `* / %` < `-` (unario) < `not`

### Acciones (7 básicas)

| Acción | Argumentos | Descripción |
|--------|------------|-------------|
| `wait(n)` | `n` turnos | Espera `n` turnos (mín 1) |
| `move(dx, dy, speed)` | -1/0/1, -1/0/1, ≥0 | Avanza hasta `speed` casillas |
| `attack(dx, dy, dmg)` | -1/0/1, -1/0/1, ≥0 | Daña en casilla adyacente |
| `consume(dx, dy, dmg, heal)` | -1/0/1, -1/0/1, ≥0, ≥0 | Ataca y cura al atacante |
| `reproduce(dx, dy, hp)` | -1/0/1, -1/0/1, ≥0 | Crea cría en casilla adyacente |
| `roar(valor)` | cualquier | Emite rugido (se oye en radio) |
| `say(texto)` | cualquier | Imprime mensaje (NO consume turno) |

### Funciones Reservadas

| Función | Retorna | Descripción |
|---------|---------|-------------|
| `see(x, y)` | `NONE=-1`, `GROUND=0`, `OBJECT=1`, `ALLY=2`, `ENEMY=3` | Qué hay en coordenadas absolutas |
| `name(x, y)` | `string` | Nombre de lo que hay en (x,y) |

### Percepciones (31, solo lectura)

| Categoría | Variables |
|-----------|-----------|
| **Yo** | `health`, `age`, `lifespan`, `vision`, `species`, `faction`, `x`, `y`, `terrain_here`, `reserve_here` |
| **Mundo** | `width`, `height`, `tick`, `total_creatures`, `total_allies`, `total_enemies`, `random` |
| **Cerca** (radio visión) | `allies_near`, `enemies_near`, `objects_near`, `enemy_dist`, `enemy_dx`, `enemy_dy`, `ally_dist`, `ally_dx`, `ally_dy`, `object_dist`, `object_dx`, `object_dy`, `roars_near`, `last_roar` |

---

## 🧪 Tests

```bash
# Todos los tests
python -m pytest lang/ -v

# Por módulo
python -m lang.test_interpreter
python -m lang.test_semantics
python -m lang.test_compiler
python -m lang.test_parser
python -m lang.test_catalog
python -m lang.test_cli
python -m world.test_world
```

---

## 🏗️ Arquitectura

```
compilador/
├── main.py                 # CLI entry point
├── lang/                   # Compilador
│   ├── lexer.py           # Tokenizer
│   ├── parser.py          # Parser (cabecera + cuerpo)
│   ├── semantics.py       # Análisis semántico
│   ├── interpreter.py     # Intérprete (100 inst/turno)
│   ├── actions.py         # 7 acciones básicas
│   ├── values.py          # Operadores + truthiness
│   ├── ast_nodes.py       # Nodos AST
│   ├── catalog.py         # Catálogo centralizado
│   ├── errors.py          # Excepciones tipadas
│   └── compiler.py        # Pipeline: lex → parse → semántica
├── world/                  # Simulación
│   ├── world.py           # Mundo, criaturas, percepciones, acciones
│   ├── creature.py        # Estado físico + ejecución
│   └── terrain.py         # Terreno (GROUND/ROCK) + reserva
└── ui/                     # Interfaz (pendiente)
```

---

## 🎯 Ejemplos

### Uruk Básico (huye si poca vida)

```instinct
creature Uruk
faction isengard
health 80
vision 6
lifespan 400
start:
if health < 20 goto flee
goto start
flee:
move(-enemy_dx, -enemy_dy, 3)
goto start
```

### Explorador (camina aleatoriamente)

```instinct
creature Explorer
faction neutral
health 30
vision 8
lifespan 500
start:
move(random % 3 - 1, random % 3 - 1, 2)
goto start
```

### Depredador (ataca enemigos cercanos)

```instinct
creature Predator
faction hunters
health 100
vision 5
lifespan 300
start:
if enemy_dist <= 1 goto attack
move(enemy_dx, enemy_dy, 2)
goto start
attack:
attack(enemy_dx, enemy_dy, 15)
goto start
```

---

## 🔧 Desarrollo

### Añadir Nueva Acción

1. Añadir a `lang/catalog.py`: `ACTIONS["nueva"] = n_args`
2. Crear clase en `lang/actions.py` heredando de `Action`
3. Registrar en `ACTION_BY_NAME`

### Añadir Nueva Percepción

1. Añadir a `PERCEPTIONS_*` en `lang/catalog.py`
2. Implementar en `world/world.py` → `update_perceptions()`

---

## 📄 Licencia

MIT License — Libre para usar, modificar y distribuir.

---

## 👤 Autor

**Sergio0307** — [GitHub](https://github.com/Sergio0307)

---

*Última actualización: 2024*