# Patrones de Diseño para el Compilador de Instinct

- **Proyecto:** Instinct (compilador de lenguaje `.ins` + simulador)
- **Ámbito:** `lang/` completo (lexer, parser, semántica, intérprete y acciones). No se analiza `world/` (simulación), aunque se mencione donde una acción interactúa con él.
- **Estado:** Ideas de arquitectura para refactorización y evolución del compilador. Ninguna es obligatoria: se incluyen por si alguna interesa. Varias resuelven problemas parecidos (por ejemplo Chain of Responsibility y Specification) y se dejan todas como alternativas.

---

## Índice

1. [Visitor](#1-visitor)
2. [Command](#2-command)
3. [Chain of Responsibility](#3-chain-of-responsibility)
4. [Result / Either](#4-result--either)
5. [Specification](#5-specification)
6. [Factory](#6-factory)
7. [Null Object](#7-null-object)
8. [Decorator](#8-decorator)
9. [Tabla resumen y recomendación final](#9-tabla-resumen-y-recomendación-final)

---

## 1. Visitor

### ¿Qué es en general?
El patrón **Visitor** separa los algoritmos (operaciones) de los objetos sobre los que operan. En lugar de que cada objeto del árbol tenga métodos como `evaluate()`, `validar()` o `imprimir()`, se define una interfaz `Visitor` con un método por tipo de nodo (`visit_numero`, `visit_binaria`, etc.). Cada nodo solo implementa `accept(visitor)` que llama al método correspondiente del visitor. Así, el tipo de nodo y el tipo de visitor se resuelven juntos (doble despacho).

### ¿Cómo se usaría en el compilador de Instinct?
Hoy en `lang/ast_nodes.py` los nodos ya contienen lógica de evaluación (`Number.evaluate`, `BinaryOp.evaluate`, `Call.evaluate`). Eso mezcla la estructura de datos con el comportamiento de ejecución.

Se aplicaría así:

1. **Quitar los métodos `evaluate` de los nodos AST.** Los nodos quedan como estructuras puras de datos (campos `left`, `right`, `op`, `name`, etc.).
2. **Crear una interfaz `ASTVisitor`** con un método `visit_*` por cada tipo de nodo.
3. **Cada nodo implementa `accept(visitor)`** que llama al método correspondiente del visitor.
4. **Crear visitors concretos:**
   - `EvaluadorVisitor`: contiene la lógica de `values.binary`, `values.unary`, resolución de variables, etc.
   - `VisitadorSemantico`: valida aridad, tipos, saltos a etiquetas, asignaciones a readonly.
   - `PrettyPrinterVisitor`: imprime el árbol legiblemente.
   - `OptimizadorVisitor`: futura etapa de optimización (doble negación, constantes, etc.).

El intérprete ya no llama a `instr.evaluate(ctx)`; en su lugar hace `instr.accept(evaluador)` y el evaluador decide qué hacer con ese nodo.

### Ventajas
- **Separa responsabilidades:** un nodo AST no debería saber cómo ejecutarse; eso le corresponde al intérprete.
- **Open/Closed:** se añade una nueva operación (ej. un formateador o un linter) creando un nuevo visitor, sin tocar los nodos.
- **Testing:** se puede crear un visitor de prueba que solo registre qué nodos se visitan, sin ejecutar nada real.

### Desventajas
- Aumenta la cantidad de clases (un visitor por operación).
- Rompe el encapsulamiento: el visitor necesita acceso público a los campos internos de los nodos.
- Si se agrega un nuevo tipo de nodo AST, hay que actualizar todos los visitors existentes.
- Para un proyecto pequeño con solo una operación (ejecutar) puede ser sobreingeniería.

### Alternativa ligera en Python
`match`/`case` (Python 3.10+) o `functools.singledispatch` dan una separación parecida entre nodos y operaciones, sin el doble despacho ni los métodos `accept`.

### Veredicto
**Recomendado a medio plazo.** El compilador ya tiene varias operaciones sobre el mismo AST (semántica, intérprete) y el acoplamiento actual (`evaluate` dentro de nodos) es deuda técnica. Es el patrón de mayor impacto para el compilador.

---

## 2. Command

### ¿Qué es en general?
El patrón **Command** encapsula una petición como un objeto. Cada comando tiene `execute()` y opcionalmente `undo()`. Un invocador ejecuta comandos sin saber qué hacen exactamente. Permite colas, logging, transacciones y deshacer/rehacer.

### ¿Cómo se usaría en el compilador de Instinct?
En `lang/actions.py` ya existe una clase base `Action` con `execute`, `check` y `apply`. Eso es muy parecido a Command, pero no está formalizado como tal. Se podría:

1. **Formalizar `Command`** con `execute()` y `undo()`.
2. **Cada acción** (`Move`, `Attack`, `Consume`, `Reproduce`, etc.) implementaría su propio `undo()` (por ejemplo, `Move` recuerda la posición anterior y puede volver; `Reproduce` eliminaría la criatura creada).
3. **Un `CommandInvoker`** gestionaría una pila de comandos ejecutados para permitir deshacer en un futuro editor/inspector de `ui/`.
4. **`Say`**, que no consume turno, podría marcarse como comando de solo lectura.
5. Con `undo()` sería posible **retroceder el tiempo** en la UI, algo interesante de ver.

### Ventajas
- Desacopla al intérprete (invocador) de la acción concreta.
- Permite deshacer/rehacer, útil si se construye un inspector visual o un editor en `ui/`.
- Posibilita colas de comandos, logging de acciones y agrupación en transacciones.

### Desventajas
- Algunas acciones son irreversibles o difíciles de deshacer (`reproduce` crea una nueva criatura; `roar` deja un registro permanente en el log del mundo).
- Añade boilerplate a acciones que hoy son simples.
- Si nunca se necesita deshacer, el patrón añade complejidad innecesaria.
- Para retroceder el tiempo en la UI, deshacer acción por acción obliga a revertir en orden inverso y a tener en cuenta las interacciones entre criaturas y el azar; guardar una copia (snapshot) del estado del mundo por tick suele ser más simple.

### Veredicto
**Parcialmente recomendado.** Mantener la estructura actual (`Action` con `execute`/`apply`) pero añadir `undo()` solo a las acciones que lo necesiten (`Move`, `Attack`, `Consume`). No implementar un `CommandInvoker` completo hasta que `ui/` lo requiera.

---

## 3. Chain of Responsibility

### ¿Qué es en general?
El patrón **Cadena de Responsabilidad** permite pasar una solicitud a lo largo de una cadena de manejadores. Cada manejador decide si procesa la solicitud o la pasa al siguiente. Se usa para pipelines de validación, filtros o middleware.

### ¿Cómo se usaría en el compilador de Instinct?
Hoy `compile_species()` ejecuta un pipeline lineal fijo: lexer → parser → semántica. Cada fase lanza su propio tipo de excepción y no hay forma sencilla de insertar validadores adicionales sin tocar esa función.

Se aplicaría así:

1. **Definir un manejador abstracto `ValidationHandler`** con referencia al siguiente y un método `manejar(species)`.
2. **Crear manejadores concretos** que validen la especie ya parseada: `ValidacionSemantica` (las comprobaciones actuales) y `ReglasPersonalizadas` (reglas nuevas). Las fases léxica y sintáctica no encajan como manejadores, porque transforman el texto en tokens y los tokens en AST en lugar de validar un resultado.
3. **Cada uno procesa o pasa al siguiente.** Pueden acumular errores o detener la cadena.
4. **Permite agregar/quitar validadores** (ej. "variables deben estar definidas antes de usarse", "daño no puede ser negativo") sin modificar el núcleo del compilador.

### Ventajas
- Pipeline configurable y extensible.
- Cada manejador tiene una sola responsabilidad.
- Se pueden agregar reglas de validación personalizadas para archivos `.ins` sin tocar el compilador base.

### Desventajas
- El orden de los manejadores es crítico y debe documentarse.
- Difícil de depurar si un manejador falla silenciosamente y pasa al siguiente.
- Para un pipeline fijo de 3 fases (léxico, sintáctico, semántico) puede ser sobrecódigo.

### Veredicto
**Recomendado para la fase semántica y reglas adicionales.** El pipeline léxico→sintáctico→semántico es tan estable que no necesita Chain of Responsibility completo, pero sí beneficia a las reglas semánticas nuevas (definición antes de uso, tipos de argumento, rangos). Resuelve un problema parecido al de Specification (sección 5): son alternativas para organizar las reglas, no hace falta usar ambas.

---

## 4. Result / Either

### ¿Qué es en general?
El patrón **Result** (o **Either**) sustituye las excepciones por un tipo de retorno explícito: `Ok(valor)` o `Error(lista_de_errores)`. En lugar de `raise`, las funciones retornan este objeto y el llamador debe inspeccionarlo antes de continuar. Es común en lenguajes funcionales (Rust, Haskell, Elm).

### ¿Cómo se usaría en el compilador de Instinct?
Hoy el compilador usa excepciones para control de flujo (`raise LexError`, `raise ParseError`, `raise SemanticErrors`). Con Result:

1. **Definir `Result[T]`** como tipo discriminado (`Ok` o `Error`).
2. **`compile_species` retornaría `Result[SpeciesDef]`** en lugar de lanzar.
3. **Cada fase (lexer, parser, semántica) encadenaría con `bind` / `flat_map`.**
4. **Los errores semánticos se acumulan naturalmente** en una lista sin necesidad de clases especiales como `SemanticErrors`.

### Ventajas
- El tipo de retorno comunica explícitamente que la función puede fallar (no se olvida manejar el error).
- No hay costo de stack trace para errores esperados.
- Más fácil de combinar con programación funcional y testing.

### Desventajas
- Cambio grande en la firma de todas las funciones del pipeline.
- Requiere educar al equipo sobre el patrón.
- **No es idiomático en Python**, donde las excepciones son la norma para errores.
- Interop con código existente que lanza excepciones requiere adaptadores constantes.

### Veredicto
**No recomendado para esta fase.** Python usa excepciones de forma idiomática y el patrón Result añadiría fricción innecesaria. Solo tendría sentido en una reescritura mayor del compilador.

---

## 5. Specification

### ¿Qué es en general?
El patrón **Specification** encapsula una regla de negocio o validación en un objeto con un método `es_satisfecha_por(candidato) -> bool` y opcionalmente `razon() -> str`. Las especificaciones se pueden combinar con operadores lógicos (`And`, `Or`, `Not`) para formar reglas compuestas.

### ¿Cómo se usaría en el compilador de Instinct?
En `lang/semantics.py`, los métodos `_check_header`, `_check_jumps`, `_check_assignments`, `_check_calls` están mezclados en una sola clase. Con Specification:

1. **Definir interfaz `Specification[T]`** con `es_satisfecha_por(candidato)` y `razon()`.
2. **Implementar especificaciones:** `CabeceraCompleta`, `ClavesNoDuplicadas`, `EtiquetasExistentes`, `NoAsignarARadonly`, `AccionValida`, `FuncionValida`, `ArgumentosCorrectos`.
3. **Combinar con `AndSpecification` y `OrSpecification`.**
4. **`SemanticAnalyzer` recibe una lista de especificaciones** y las evalúa todas, acumulando fallos con sus razones.

### Ventajas
- Reglas de validación compuestas, reutilizables y testeables aisladamente.
- Fácil de añadir, quitar o reordenar reglas sin tocar `SemanticAnalyzer`.
- Cada especificación tiene una razón de fallo clara y documentada.

### Desventajas
- Más clases e indirección para reglas que hoy son simples y estáticas.
- Puede ser excesivo si solo hay 4-5 reglas de validación que no cambian.

### Veredicto
**Recomendado.** Es ideal para abordar las mejoras pendientes (variables no inicializadas, tipos de argumento, rangos de daño/curación) como especificaciones independientes sin ensuciar la clase principal.

---

## 6. Factory

### ¿Qué es en general?
El patrón **Factory** centraliza la creación de objetos. En lugar de llamar directamente a constructores dispersos, se usa una fábrica que decide qué clase instanciar y aplica valores por defecto consistentes.

### ¿Cómo se usaría en el compilador de Instinct?
Ya existe `ACTION_BY_NAME` en `lang/actions.py`, que funciona como una fábrica de acciones. Pero la creación de `Token` y de nodos AST está dispersa (constructores directos en el parser y lexer). Se podría:

1. **`TokenFactory`:** centraliza la creación de `Token`, validando tipos y asignando `line`/`col`/`filename` correctamente.
2. **`NodeFactory`:** centraliza la creación de nodos AST, asegurando que `line` nunca quede en `0` por defecto (corrige el problema de línea 0).
3. **Las fábricas pueden inyectarse como mocks en tests.**

### Ventajas
- Punto único de cambio para la creación de objetos.
- Consistencia en campos como `line`, `col`, `filename`.
- Fácil de probar con fábricas simuladas.

### Desventajas
- Capa de indirección adicional para objetos simples (Token es un dataclass).
- Para un proyecto pequeño puede ser sobreingeniería.

### Veredicto
**Parcialmente recomendado.** `ACTION_BY_NAME` ya funciona como factory para acciones. Para `Token` y nodos AST, una factory simple ayuda a centralizar valores por defecto (especialmente para corregir que `line` sea 0). Si el único objetivo es evitar `line=0`, es más simple hacer `line` un argumento obligatorio, sin valor por defecto, en el constructor de los nodos.

---

## 7. Null Object

### ¿Qué es en general?
El patrón **Null Object** sustituye referencias `None` por un objeto que implementa la misma interfaz pero con comportamiento "vacío" o seguro (retorna 0, cadena vacía, false, o no-op). Evita comprobaciones `if valor is None` en todo el código.

### ¿Cómo se usaría en el compilador de Instinct?
Hoy `EvalContext.resolve` lanza `RuntimeFault("variable ... leída antes de asignarse")` si una variable no existe, y `world.perception` devuelve `0` por defecto. Con Null Object:

1. **Definir `UndefinedValue`** como objeto con comportamiento seguro (`0` en operaciones numéricas, `""` en strings, `False` en truthiness).
2. **`resolve` retornaría `UndefinedValue`** en lugar de lanzar, y el intérprete decidirá si tratarlo como error o como valor por defecto.
3. **Para etiquetas faltantes, un `NullLabel`** que haga no-op en saltos.

### Ventajas
- Elimina comprobaciones `if valor is None` en todo el intérprete.
- Comportamiento predecible para valores faltantes.
- Menos excepciones de control de flujo.

### Desventajas
- Puede silenciar errores reales: una variable no inicializada **debe** ser error, no `0`.
- Dificulta distinguir "valor legítimamente cero" de "valor no definido".
- Requiere convenciones claras sobre cuándo usar Null Object vs excepción.

### Veredicto
**No recomendado para variables no inicializadas** (debe ser error explícito). Sí podría usarse para percepciones opcionales donde un default tiene sentido semántico, pero hoy `world.perception` ya devuelve `0` por defecto, así que no aporta mucho nuevo.

---

## 8. Decorator

### ¿Qué es en general?
El patrón **Decorator** envuelve un objeto con otro que implementa la misma interfaz, añadiendo comportamiento antes o después de delegar. Permite añadir responsabilidades (logging, validación, timing) sin modificar la clase original.

### ¿Cómo se usaría en el compilador de Instinct?
Si se quiere añadir logging, validación de rangos o medición de tiempo a las acciones, hoy hay que modificar la clase o crear subclases. Con Decorator:

1. **`ActionDecorator` implementa `Action`** y contiene otra `Action`.
2. **Decoradores concretos:** `LoggedAction` (registra entrada/salida), `ValidatedAction` (valida rangos antes de ejecutar), `TimedAction` (mide duración).
3. **Se combinan dinámicamente:** `LoggedAction(ValidatedAction(Move()))`.

### Ventajas
- Comportamiento transversal (logging, timing) sin modificar la acción base.
- Composición dinámica en runtime.
- Cada decorador tiene una sola responsabilidad.

### Desventajas
- Aumenta la cantidad de clases.
- El orden de los decoradores importa y puede ser confuso.
- Depuración más compleja (stack de decoradores).

### Veredicto
**Recomendado si se añade inspector/UI.** Útil si se construye un inspector en `ui/` que necesita trazar qué acciones ejecutan las criaturas. Por ahora no es prioritario.

---

## 9. Tabla resumen y recomendación final

| Patrón | ¿Dónde aplicar? | ¿Recomendado? | Por qué |
|--------|----------------|---------------|---------|
| **Visitor** | `ast_nodes.py`, intérprete, semántica | ✔ Medio plazo | Separa estructura de datos de operaciones; evita `evaluate` dentro de nodos |
| **Command** | `actions.py` | Parcial | Ya existe `Action`; solo añadir `undo()` a acciones reversibles |
| **Chain of Responsibility** | `semantics.py`, reglas de validación | ✔ Para reglas nuevas | Pipeline de validaciones configurable sin tocar el núcleo |
| **Result/Either** | `compiler.py` | No | No es idiomático en Python; requiere reescritura grande |
| **Specification** | `semantics.py` | ✔ | Reglas de validación compuestas y testeables aisladamente |
| **Factory** | `tokens.py`, `ast_nodes.py` | Parcial | Ya hay `ACTION_BY_NAME`; útil para centralizar `line`/`col` de nodos |
| **Null Object** | `interpreter.py`, valores faltantes | No | Silenciaría errores de variables no inicializadas |
| **Decorator** | `actions.py` | Sí (si hay UI) | Útil para logging/timing en un futuro inspector |

### Orden sugerido (si se decide adoptar alguno)

1. **Visitor** — separa el intérprete de los nodos AST (mayor impacto en deuda técnica).
2. **Specification** (o Chain of Responsibility, que resuelve lo mismo) — reglas de semántica compuestas sin ensuciar `SemanticAnalyzer`.
3. **Factory (nodos/tokens)** — centraliza valores por defecto como `line` y `col`.
4. **Command (parcial)** — añadir `undo()` a acciones reversibles solo si `ui/` lo requiere.

Decorator queda para cuando exista un inspector en `ui/`. Result y Null Object se descartan por ahora.
