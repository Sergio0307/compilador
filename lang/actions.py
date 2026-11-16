"""Las siete acciones básicas del lenguaje Instinct (spec 2.4).

Cada acción es una subclase de Action que sabe validar sus argumentos en
tiempo de ejecución y aplicar su efecto sobre el mundo. Añadir una acción
nueva al lenguaje = escribir una clase más y registrarla abajo, sin tocar
las existentes (sección 5 de la spec: nada de cadenas de ifs).

El intérprete evalúa los argumentos y llama a `execute(ctx, args, line)`.
Esta devuelve si la acción consume el turno (todas salvo `say`).
"""

from abc import ABC, abstractmethod

from lang.errors import RuntimeFault
from lang.values import require_numbers


def _require_numbers(args, line=None, col=None, filename=None, context=""):
    """Valida que todos los args sean números (delegado a values.require_numbers)."""
    require_numbers(args, line=line, col=col, filename=filename, context=context)


def _require_directions(dx, dy, line=None, col=None, filename=None, context=""):
    """Valida que dx, dy sean números y estén en {-1, 0, 1}."""
    _require_numbers([dx, dy], line=line, col=col, filename=filename, context=context)
    for value, name in ((dx, "dx"), (dy, "dy")):
        if value not in (-1, 0, 1):
            raise RuntimeFault(
                f"dirección fuera de rango ({value}): {name} debe estar en {{-1, 0, 1}}",
                line=line, col=col, filename=filename,
            )


class Action(ABC):
    """Una acción del catálogo. `name` y `arity` espejan lang.catalog.ACTIONS."""

    name = ""
    arity = 0
    consumes_turn = True

    def execute(self, ctx, args, line=None, col=None, filename=None):
        """Valida la aridad y los argumentos, aplica el efecto y dice si
        consume el turno. `ctx` da acceso a criatura, mundo y estado."""
        if len(args) != self.arity:
            raise RuntimeFault(
                f"la acción '{self.name}' espera {self.arity} argumentos, "
                f"se encontraron {len(args)}",
                line=line, col=col, filename=filename,
            )
        self.check(ctx, args, line, col, filename)
        self.apply(ctx, args, line, col, filename)
        return self.consumes_turn

    def check(self, ctx, args, line=None, col=None, filename=None):
        """Validaciones de runtime comunes; las subclases amplían."""

    @abstractmethod
    def apply(self, ctx, args, line=None, col=None, filename=None):
        """Aplica el efecto de la acción sobre el mundo."""


class Wait(Action):
    """wait(n): no hace nada durante n turnos seguidos (n >= 1)."""
    name = "wait"
    arity = 1

    def check(self, ctx, args, line=None, col=None, filename=None):
        _require_numbers(args, line=line, col=col, filename=filename)
        if args[0] < 1:
            raise RuntimeFault(
                "wait espera n >= 1",
                line=line, col=col, filename=filename,
            )

    def apply(self, ctx, args, line=None, col=None, filename=None):
        turns = args[0]  # Ya validado >= 1
        ctx.state.waiting = turns - 1


class Move(Action):
    """move(dx, dy, speed): avanza hasta speed casillas en (dx, dy)."""
    name = "move"
    arity = 3

    def check(self, ctx, args, line=None, col=None, filename=None):
        _require_numbers(args, line=line, col=col, filename=filename)
        _require_directions(args[0], args[1], line=line, col=col, filename=filename)

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.move(ctx.creature, *args)


class Attack(Action):
    """attack(dx, dy, damage): golpea la casilla adyacente (0,0 = la de abajo)."""
    name = "attack"
    arity = 3

    def check(self, ctx, args, line=None, col=None, filename=None):
        _require_numbers(args, line=line, col=col, filename=filename)
        _require_directions(args[0], args[1], line=line, col=col, filename=filename)

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.attack(ctx.creature, *args)


class Consume(Action):
    """consume(dx, dy, damage, heal): como attack y además gana heal de vida."""
    name = "consume"
    arity = 4

    def check(self, ctx, args, line=None, col=None, filename=None):
        _require_numbers(args, line=line, col=col, filename=filename)
        _require_directions(args[0], args[1], line=line, col=col, filename=filename)

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.consume(ctx.creature, *args)


class Reproduce(Action):
    """reproduce(dx, dy, health): crea una cría en la casilla adyacente."""
    name = "reproduce"
    arity = 3

    def check(self, ctx, args, line=None, col=None, filename=None):
        _require_numbers(args, line=line, col=col, filename=filename)
        _require_directions(args[0], args[1], line=line, col=col, filename=filename)

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.reproduce(ctx.creature, *args)


class Roar(Action):
    """roar(value): emite un rugido; acepta cualquier valor."""
    name = "roar"
    arity = 1

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.roar(ctx.creature, args[0])


class Say(Action):
    """say(value): muestra un texto. Única acción que NO consume turno."""
    name = "say"
    arity = 1
    consumes_turn = False

    def apply(self, ctx, args, line=None, col=None, filename=None):
        ctx.world.say(ctx.creature, args[0])


# Registro para el despacho del intérprete: nombre -> instancia.
ACTION_BY_NAME = {a.name: a for a in (Wait(), Move(), Attack(), Consume(),
                                       Reproduce(), Roar(), Say())}