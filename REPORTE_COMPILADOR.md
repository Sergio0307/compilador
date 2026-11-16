# Reporte de Análisis del Compilador — Proyecto Instinct

- **Ámbito revisado:** `lang/` (lexer, parser, ast_nodes, tokens, catalog, semantics, compiler, interpreter, actions, values, errors) y `main.py`.
- **Ámbito excluido:** `world/` (simulación, criaturas, terreno) — no se analiza en este documento.
- **Modelo usado para el análisis:** nemotron-3.5-super-vl-120b-a12b (6 subagentes en paralelo).
- **Código analizado:** implementación en Python de un estudiante.

---

## Estructura del reporte

| Sección | Contenido |
|---------|-----------|
| 1. Lexer | Problemas lógicos, malas prácticas, buenas prácticas, opciones de solución |
| 2. Parser + AST y casos límite | Casos límite de ejecución detectados al revisar el AST (el parser no tuvo hallazgos relevantes) |
| 3. Intérprete + Acciones + Valores | Idem |
| 4. Arquitectura + CLI + Tests | Idem |
| 5. Plan de acción recomendado | Prioridades y orden de corrección |
| 6. Patrones de diseño | Resumen; el detalle está en `PATRONES_DISENO_COMPILADOR.md` |

Cada problema incluye:
- **Ubicación:** archivo y líneas aproximadas.
- **Descripción:** qué ocurre y por qué es un problema.
- **Opciones de solución:** varias alternativas.
- **✔ Recomendada:** la opción sugerida para aplicar primero.

**Importancia (★):** marca de prioridad en títulos de sección y de problema. Más estrellas = más importante corregirlo; sin estrellas = mejora opcional o menor.

---

## 1. Lexer (`lang/lexer.py`, `lang/tokens.py`, `lang/errors.py`)
### 1.1 Números con caracteres no decimales aceptados como válidos ★★

**Ubicación:** `lexer.py:140-146` (`read_number`), `parser.py:364-366`

**Descripción:** `read_number` consume cualquier secuencia de caracteres para los que `isdigit()` es verdadero, y eso incluye dígitos Unicode que no son ASCII. Algunos (por ejemplo `²`) hacen fallar `int(value)` en el parser con un `ValueError` crudo; otros (por ejemplo los dígitos arábigos orientales, como `٣`) se aceptan en silencio como números válidos, algo probablemente no intencionado.

**Opciones:**
1. No cambiar nada (dejar que el parser lance `ValueError` crudo). **No recomendado:** expone un traceback interno al usuario.
2. Restringir `read_number` a dígitos ASCII (`'0' <= ch <= '9'`) y rechazar cualquier otro carácter con `LexError` claro. **Recomendada:** falla temprano y con mensaje legible.
3. Aceptar solo enteros ASCII y delegar decimales/notación científica a una fase posterior (si se añaden).

**✔ Recomendada:** Opción 2. Cambiar `isdigit()` por comprobación de rango ASCII y lanzar `LexError("Número inválido")` para caracteres no esperados.

---

### 1.2 `!` solitario no reconocido; no se sugiere `!=` ★
**Ubicación:** `lexer.py:112-123`

**Descripción:** El único símbolo de dos caracteres que empieza con `!` es `!=`. Si el fuente contiene `!` solo (error tipográfico o intento de operador unario `!`), el lexer lanza `LexError("Carácter inesperado '!'")` sin sugerir `!=`.

**Opciones:**
1. Dejar como está. Mensaje crudo pero funcional.
2. Añadir caso especial: si `ch == '!'`, lanzar `LexError("Carácter inesperado '!'. ¿Quiso decir '!='?", ...)`. **Recomendada:** mejora la experiencia del programador `.ins` sin costo.
3. Implementar operador unario `!` en el lenguaje (requiere cambios en parser, semántica e intérprete). Sobreingeniería para esta fase.

**✔ Recomendada:** Opción 2.

---

### 1.3 Valor del token `NEWLINE` es literal `"\\n"` (dos caracteres) ★
**Ubicación:** `lexer.py:93, 133`

**Descripción:** `NEWLINE` se añade con valor `"\\n"` (barra invertida + n), no el carácter real de salto de línea ni una cadena vacía. `EOF` lleva `""`. Quien lea el valor esperando el carácter de salto de línea real (`value == "\n"`) fallará silenciosamente. Como el tipo del token ya identifica el salto de línea, el valor no debería cargar información.

**Opciones:**
1. Cambiar valor de `NEWLINE` a `"\n"` (carácter real). Consistencia con la semántica del nombre del token.
2. Cambiar valor de `NEWLINE` a `""` (vacío), igual que `EOF`. **Recomendada:** `NEWLINE` es un marcador estructural, no necesita valor semántico; evitar confusión con saltos de línea reales en strings.
3. Dejar `"\\n"` y documentar que es un valor sintético. No recomendado: fuente de bugs silenciosos.

**✔ Recomendada:** Opción 2.

---

### 1.4 `peek(offset)` sin validación de offset negativo ★
**Ubicación:** `lexer.py:50-53`

**Descripción:** Si `offset` es negativo, `i = self.pos + offset` puede ser negativo y `self.src[i]` en Python accede desde el final del string (índice negativo válido), devolviendo un carácter incorrecto sin error.

**Opciones:**
1. Rechazar `offset < 0` con `ValueError` interno. **Recomendada:** detección temprana de uso incorrecto de la API.
2. Acotar `i` a `[0, len)` con `max(0, min(i, len(self.src) - 1))`. Silencioso; puede ocultar bugs.
3. No hacer nada. Riesgo de lecturas incorrectas.

**✔ Recomendada:** Opción 1.

---

### 1.5 `LexError` no tipifica el tipo de error léxico 

**Ubicación:** `errors.py:19-20` (y uso en `lexer.py:126-129, 163-166, 169-171`)

**Descripción:** `LexError` es un `pass` puro sobre `InstinctError`. No hay subcategorías (carácter inesperado, string sin cerrar, número inválido). El consumidor no puede distinguir tipos por clase, solo por mensaje de texto.

**Opciones:**
1. Añadir campo `code: str` a `LexError` (ej. `"E_LEX_001"`). **Recomendada:** permite reaccionar por código sin parsear mensajes.
2. Crear subcategorías (`UnexpectedCharacterError`, `UnterminatedStringError`, etc.). Más verboso; útil si el IDE o CLI quiere resaltar distinto cada tipo.
3. Dejar como está. Suficiente para un compilador pequeño, pero difícil de escalar.

**✔ Recomendada:** Opción 1 (campo `code`).

---

### 1.6 Falta de validación de entrada en `Lexer.__init__` ★
**Ubicación:** `lexer.py:40-46`

**Descripción:** No se valida que `source` sea `str`. Si se pasa `None` o `bytes`, `len(self.src)` o `self.src[i]` lanzan `TypeError` crudo en lugar de un error controlado.

**Opciones:**
1. Añadir `if not isinstance(source, str): raise TypeError(...)`. **Recomendada:** falla temprano con mensaje claro.
2. Convertir automáticamente con `str(source)`. Oculta errores de llamada.
3. No hacer nada.

**✔ Recomendada:** Opción 1.

---

### 1.7 `tester_lexer.py` no es un test ejecutable

**Ubicación:** `lang/tester_lexer.py:5`

**Descripción:** Usa import relativo `from .errors import LexError` pero se ejecuta como script (`python tester_lexer.py`), lo que falla con `ImportError`. Además no tiene `assert`; solo imprime tokens por consola.

**Opciones:**
1. Cambiar a `from lang.errors import LexError` y convertirlo en un test real con asserts. **Recomendada** si se quiere conservar el archivo.
2. Eliminar `tester_lexer.py` y crear `test_lexer.py` propiamente dicho con pytest. **Recomendada** a largo plazo: estándar del proyecto.
3. Dejar como script de depuración manual, documentado como tal.

**✔ Recomendada:** Opción 2 (crear `test_lexer.py` con pytest y eliminar o depurar `tester_lexer.py`).

---

## 2. Parser + AST y casos límite de ejecución (`lang/parser.py`, `lang/ast_nodes.py`, `lang/interpreter.py`, `lang/actions.py`) ★

> Los hallazgos del parser y del AST fueron menores (aclaraciones que no afectan el funcionamiento) y se omiten a propósito. Esta sección reúne casos límite de ejecución detectados durante la revisión.
### 2.1 `KeyError` no controlado en etiquetas de salto en tiempo de ejecución

**Ubicación:** `interpreter.py:181, 186` (`_do_goto`, `_do_if`) — aunque la fase semántica valida que las etiquetas existan, el intérprete accede con `program.labels[instr.label]` sin `.get()`.

**Descripción:** Si alguna ruta de construcción de `Program` salta la validación semántica (uso directo de la API interna), un `goto` o `ifgoto` a etiqueta inexistente lanza `KeyError` crudo en lugar de `RuntimeFault`, rompiendo el contrato de que el intérprete solo lanza errores controlados.

**Opciones:**
1. Cambiar a `program.labels.get(instr.label)` y lanzar `RuntimeFault("etiqueta inexistente ...")` si es `None`. **Recomendada:** cumple el contrato de errores controlados.
2. Dejar `KeyError`; confiar en que la semántica siempre valida antes. Frágil ante uso directo de la API.
3. Validar en `Program.from_species` que todas las etiquetas referenciadas existan. Duplica la semántica.

**✔ Recomendada:** Opción 1.

---

### 2.2 `wait(0)` y `wait(negativo)` sin validación clara ★
**Ubicación:** `actions.py:74-78` (`Wait.apply`), `interpreter.py:148-150`

**Descripción:** `wait(n)` con `n < 1` se normaliza a `turns = 1`, y `waiting = turns - 1` da `0`: `wait(0)`, `wait(-3)` y `wait(1)` se comportan igual (la criatura no espera ningún turno extra). No hay validación explícita ni se documenta el comportamiento para `n <= 0`, así que un valor mal calculado pasa sin aviso.

**Opciones:**
1. Rechazar `n <= 0` con `RuntimeFault("wait espera n >= 1")`. **Recomendada:** falla temprano y obliga al programador a ser explícito. Verificar antes que el enunciado del lenguaje no defina otro comportamiento.
2. Mantener normalización implícita a 1 pero documentarlo en el docstring y en la semántica. Menos estricto.
3. Permitir `wait(0)` como "no-op que consume el turno actual". Semánticamente extraño.

**✔ Recomendada:** Opción 1.

---

## 3. Intérprete + Acciones + Valores (`lang/interpreter.py`, `lang/actions.py`, `lang/values.py`, `lang/errors.py`) ★★★
### 3.1 Validaciones de "es número" duplicadas en 4 sitios con mensajes distintos

**Ubicación:** `actions.py:17-23` (`_require_numbers`), `actions.py:26-34` (`_require_directions`), `interpreter.py:33-38` (`_require_coords`), `values.py:47-50` (`_check_number`)

**Descripción:** Cada acción numérica (`Wait`, `Move`, `Attack`, `Consume`, `Reproduce`) llama a `_require_numbers`. `_require_coords` duplica la idea para `see`/`name`. `values._check_number` es casi idéntico pero con mensaje distinto. Mantenimiento disperso: cambiar el mensaje o la lógica requiere editar varios sitios.

**Opciones:**
1. Unificar en una sola función `require_numbers(args, line, context_name="")` en `values.py` o `actions.py`, reusada por todas. **Recomendada:** DRY, un punto de cambio.
2. Mantener las funciones separadas, pero que construyan el mensaje desde un único helper común. Menos intrusivo, aunque deja la validación duplicada.
3. Dejar como está. Funciona; solo cuesta mantenimiento si cambian los mensajes.

**✔ Recomendada:** Opción 1.

---

### 3.2 Manejo de errores inconsistente: `col` y `filename` nunca se llenan en `RuntimeFault` ★
**Ubicación:** `errors.py:1-16` define `line`, `col`, `filename`; `interpreter.py` y `actions.py` solo pasan `line` en la mayoría de `raise RuntimeFault(...)`.

**Descripción:** Parte de la infraestructura de `InstinctError` (`col`, `filename`) está muerta en el intérprete y las acciones. Los errores de runtime no reportan columna ni archivo de forma consistente.

**Opciones:**
1. Llenar `col` y `filename` en todos los `raise RuntimeFault` del intérprete y acciones (pasar `instr.line`, `instr.col` si existe, y `filename` del contexto). **Recomendada:** mensajes de error completos y consistentes.
2. Dejar solo `line` y eliminar `col`/`filename` de `InstinctError`. Simplifica pero pierde información útil.
3. Rellenar `col`/`filename` solo en errores críticos (división por cero, etiqueta inexistente). Cobertura parcial.

**✔ Recomendada:** Opción 1.

---

### 3.3 `_fetch` muta `state.pc` antes de retornar la instrucción ★★
**Ubicación:** `interpreter.py:163-167`

**Descripción:** `_fetch` comprueba `state.pc >= len(...)` y reinicia a `start` como efecto lateral, antes de devolver la instrucción. Un método llamado "fetch" no debería tener efectos laterales de salto de control; confunde la lectura.

**Opciones:**
1. Separar responsabilidades: un método `peek_instruction()` que solo lee, y `advance_pc()` llamado por cada manejador. Mayor refactor. **Recomendada** a largo plazo.
2. Mover la comprobación de reinicio al final de cada manejador de salto (`_do_goto`, `_do_if`) y al inicio del bucle, dejando `_fetch` como lectura pura simple. Menor cambio. **Recomendada** para esta fase.
3. Dejar como está. Funciona pero es confuso.

**✔ Recomendada:** Opción 2 ahora (menor cambio) y Opción 1 si más adelante se refactoriza el intérprete.

---

## 4. Arquitectura + CLI + Tests (`main.py`, `lang/compiler.py`, `README.md`, tests)

### 4.1 Código de salida inconsistente en `main.py`

**Ubicación:** `main.py:58-62` (`return 1`) vs `main.py:34, 37` (`raise SystemExit(1)`)

**Descripción:** Cuando no hay casillas libres, `main` hace `return 1`; en otros errores usa `raise SystemExit(1)`. Aunque `sys.exit(main())` propaga el código, los estilos son inconsistentes.

**Opciones:**
1. Unificar todo a `raise SystemExit(1)`. **Recomendada:** estilo consistente, salida explícita.
2. Unificar todo a `return 1` y quitar `sys.exit`. Menos explícito para código de salida.
3. Dejar como está. Funciona pero confuso para mantenedores.

**✔ Recomendada:** Opción 1.

---

### 4.2 Ninguna validación de rango de argumentos CLI (`--ticks`, `--width`, `--height`)

**Ubicación:** `main.py:45-49`

**Descripción:** `--ticks 0` o negativo → bucle no ejecuta rondas, imprime "fin en tick 0", sale con código 0 (falso éxito). `--width -5` → `range()` vacío o inesperado sin mensaje claro.

**Opciones:**
1. Añadir validador `type` o chequeo post-`parse_args` que exija `>= 1` y salga con `SystemExit(1)` + mensaje en `stderr`. **Recomendada:** entrada inválida rechazada temprano.
2. Permitir valores <= 0 y dejar que el mundo lo maneje. Genera comportamientos silenciosos.
3. Usar `choices` con rango finito. Demasiado restrictivo.

**✔ Recomendada:** Opción 1.

---

### 4.3 `cargar()` deja escapar excepciones no controladas

**Ubicación:** `main.py:27-37`

**Descripción:** Solo atrapa `OSError` e `InstinctError`. Excepciones de programación interna (`KeyError`, `AttributeError`, `ValueError`, `IndexError`) terminan con traceback crudo.

**Opciones:**
1. Añadir `except Exception as error: print(...); raise SystemExit(1)` como último recurso. **Recomendada:** usuario nunca ve traceback interno.
2. No atrapar genérico; dejar que bubble up. Útil en desarrollo, malo en producción/CLI.
3. Atrapar solo los tipos conocidos adicionales (`KeyError`, `ValueError`). Cobertura parcial.

**✔ Recomendada:** Opción 1 (con logging opcional para depuración).

---

### 4.4 `free_cells()` recalculado por especie dentro del bucle

**Ubicación:** `main.py:57-63`

**Descripción:** `cells = world.free_cells()` se ejecuta dentro del bucle `for path, sp in species`, recorriendo todo el terreno y criaturas por cada especie. O(N·W·H) en lugar de O(W·H) + actualizaciones incrementales.

**Opciones:**
1. Calcular `free_cells()` una vez antes del bucle y mantener un conjunto de libres actualizado tras cada `add_creature`. **Recomendada:** mejora de rendimiento lineal en el número de especies.
2. Dejar como está; mapas pequeños no notan la diferencia. Técnica de deuda aceptable temporalmente.
3. Mover la lógica de colocación al mundo (`world.place_creatures(species_list)`). Mayor refactor de arquitectura.

**✔ Recomendada:** Opción 1.

---

### 4.5 Ausencia de tests de integración CLI

**Ubicación:** `lang/test_*.py` y `world/test_world.py` (ninguno invoca `main()`)

**Descripción:** No existe test que invoque `main()` o `python main.py archivo.ins ...` y verifique salida por consola, códigos de salida, o formato del log. La superficie de usuario real tiene cobertura cero.

**Opciones:**
1. Crear `lang/test_cli.py` (o `tests/test_cli.py`) con pytest + `capsys`, invocando `main([...])` y verificando `stdout`/`stderr`/código de retorno. **Recomendada:** cubre la principal superficie de usuario.
2. Crear tests de subprocesso llamando a `python main.py`. Más realista pero más lento y frágil por rutas.
3. No hacer nada. Deja la CLI sin red de seguridad.

**✔ Recomendada:** Opción 1.

---

### 4.6 `README.md` de 3 líneas y sin ejemplos `.ins`

**Ubicación:** `README.md:1-3`

**Descripción:** Solo tiene 3 líneas sin explicar instalación, uso, sintaxis de `.ins`, ni ejemplos. No hay archivos `.ins` en el repositorio.

**Opciones:**
1. Escribir `README.md` completo: propósito, instalación, cómo ejecutar, sintaxis del lenguaje (cabecera, etiquetas, instrucciones, acciones, funciones, constantes), ejemplos de `.ins`, cómo correr tests. **Recomendada:** esencial para onboarding.
2. Añadir carpetas `examples/` con 3-5 `.ins` y un `README` mínimo. Complemento de la opción 1.
3. Dejar como está. Proyecto inaccesible para nuevos usuarios.

**✔ Recomendada:** Opción 1 (+ opcionalmente 2).

---

### 4.7 Sin empaquetado ni punto de entrada CLI

**Ubicación:** raíz del repositorio (no hay `pyproject.toml`, `setup.py`, `requirements.txt`)

**Descripción:** No se puede instalar con `pip install .` ni definir un comando `instinct` en el PATH. Funciona solo como carpeta suelta.

**Opciones:**
1. Añadir `pyproject.toml` con dependencias y punto de entrada `instinct = main:main`. **Recomendada:** estándar moderno Python.
2. Añadir `setup.py` (estilo legacy). Funciona pero menos recomendado hoy.
3. Dejar como está. Solo ejecutable como script desde la raíz.

**✔ Recomendada:** Opción 1.

---

## 5. Plan de acción recomendado

El orden sale de las marcas ★ de arriba.

1. **Primero (★★):** 1.1, validación de dígitos en `read_number`; y 3.3, `_fetch` modifica `state.pc` (aplicar la Opción 2).
2. **Luego (★):** 1.2, 1.3, 1.4 y 1.6 (lexer; cambios pequeños y aislados), 2.2 (`wait`) y 3.2 (`col`/`filename` en `RuntimeFault`).
3. **Sin marca (cuando haya tiempo):** 1.5, 1.7, 2.1, 3.1 y 4.1 a 4.7.

Si se va a tocar el intérprete (3.3, 3.2), conviene tener antes tests que lo respalden: 1.7 (tests del lexer) y 4.5 (tests de la CLI).

---

## 6. Patrones de diseño

El detalle de cada patrón (qué es, cómo se aplicaría en el compilador, ventajas, desventajas y veredicto) está en `PATRONES_DISENO_COMPILADOR.md`. Ninguno es obligatorio: son ideas por si alguno interesa.

| Patrón | Dónde | Complejidad | Impacto | Recomendado |
|--------|-------|-------------|---------|-------------|
| Visitor | AST (`ast_nodes.py`) | Media | Alto | ✔ Medio plazo |
| Command | Acciones (`actions.py`) | Media | Medio | Parcial (solo `undo`) |
| Chain of Responsibility | Validaciones semánticas | Baja | Medio | ✔ Para reglas nuevas |
| Result/Either | Pipeline de compilación | Alta | Alto | No (Python usa excepciones) |
| Specification | Reglas de semántica | Baja | Medio | ✔ |
| Factory | Tokens, nodos, acciones | Baja | Bajo | Parcial (ya hay `ACTION_BY_NAME`) |
| Null Object | Valores faltantes | Baja | Bajo | No (para errores de variable) |
| Decorator | Acciones con logging/timing | Media | Bajo | Sí, si se añade inspector |

**Recomendación general:** si se quiere adoptar alguno, empezar por **Visitor** (separa el intérprete de los nodos AST) y **Specification** (reglas de semántica compuestas). Estos dos abordan la deuda técnica más importante sin reescribir todo el compilador.
