"""Fase 4: intérprete de Instinct (spec 2.7).

Ejecuta un turno completo de una criatura ya compilada, con su presupuesto
de 100 instrucciones. El mundo (world/) llama a
`Interpreter.run_turn(creature, world)`; aquí no se conoce el terreno ni la
simulación, solo el contrato que ya usan los nodos del AST y las acciones:

    ctx.resolve / ctx.binary / ctx.unary / ctx.call_function   (ast_nodes)
    ctx.creature / ctx.world / ctx.state                       (actions)

Las tres piezas:

    Program            aplanado de bloques -> instrucciones + etiquetas
    CreatureExecution  estado persistente entre turnos (pc, variables, waiting)
    EvalContext        el contrato de arriba

Nada de esto importa world/: el mundo entra por parámetro.
"""

from lang.ast_nodes import Goto, IfGoto, Assign, Call
from lang.catalog import CONSTANTS, PERCEPTIONS
from lang.errors import RuntimeFault
from lang.values import binary, unary, is_truthy
from lang.actions import ACTION_BY_NAME

MAX_INSTRUCTIONS = 100   # spec 2.7


# --------------------------------------------------------------------------
# Funciones reservadas (spec 2.6)
# --------------------------------------------------------------------------

def _require_coords(fname, x, y, line):
    """see()/name() esperan coordenadas numéricas, no texto."""
    if isinstance(x, str) or isinstance(y, str):
        raise RuntimeFault(
            f"la función '{fname}' espera coordenadas numéricas", line=line
        )


def _see(ctx, args, line):
    x, y = args
    _require_coords("see", x, y, line)
    return ctx.world.see(ctx.creature, x, y)


def _name(ctx, args, line):
    x, y = args
    _require_coords("name", x, y, line)
    return ctx.world.name_at(ctx.creature, x, y)


FUNCTION_BY_NAME = {"see": _see, "name": _name}


# --------------------------------------------------------------------------
# Programa y estado de la criatura
# --------------------------------------------------------------------------

class Program:
    """Instrucciones lineales de una especie y dónde caen sus etiquetas.

    Los bloques vienen en orden de inserción y el primero es 'start:'
    (garantiza el parser), así que aplanar es directo. Las etiquetas nunca
    están dentro de `instructions`: son fronteras de bloque, por eso no
    hace falta un handler para Label.
    """

    def __init__(self, instructions, labels):
        self.instructions = instructions
        self.labels = labels

    @classmethod
    def from_species(cls, species):
        instructions, labels = [], {}
        for label, block in species.blocks.items():
            labels[label] = len(instructions)
            instructions.extend(block.instructions)
        return cls(instructions, labels)

    def __len__(self):
        return len(self.instructions)


class CreatureExecution:
    """Estado de ejecución de una criatura, persistente entre turnos."""

    def __init__(self, program, entry="start"):
        self.program = program
        self.pc = program.labels.get(entry, 0)   # índice en instructions
        self.variables = {}                       # memoria propia
        self.waiting = 0                          # turnos dormidos por wait(n)


# --------------------------------------------------------------------------
# Contexto de evaluación: el contrato de los .evaluate y de las acciones
# --------------------------------------------------------------------------

class EvalContext:
    def __init__(self, creature, world, state):
        self.creature = creature
        self.world = world
        self.state = state

    def resolve(self, name, line=None):
        """Variable propia -> constante -> percepción; si no, error."""
        if name in self.state.variables:
            return self.state.variables[name]
        if name in CONSTANTS:
            return CONSTANTS[name]
        if name in PERCEPTIONS:
            return self.world.perception(self.creature, name)
        raise RuntimeFault(
            f"variable '{name}' leída antes de asignarse", line=line
        )

    def binary(self, op, a, b, line=None):
        return binary(op, a, b, line)

    def unary(self, op, value, line=None):
        return unary(op, value, line)

    def call_function(self, name, arg_values, line=None):
        impl = FUNCTION_BY_NAME.get(name)
        if impl is None:
            raise RuntimeFault(f"función desconocida '{name}'", line=line)
        return impl(self, arg_values, line)


# --------------------------------------------------------------------------
# Intérprete
# --------------------------------------------------------------------------

class Interpreter:
    def __init__(self):
        self.actions = ACTION_BY_NAME
        self._handlers = {                 # despacho por tipo, sin ifs
            Goto:   self._do_goto,
            IfGoto: self._do_if,
            Assign: self._do_assign,
            Call:   self._do_call,
        }

    def run_turn(self, creature, world):
        """Ejecuta el turno actual. Puede lanzar RuntimeFault: el mundo lo
        captura, mata al bicho y lo registra."""
        state = creature.execution
        if state.waiting > 0:              # aún dormido: se salta el turno
            state.waiting -= 1
            return
        if not state.program.instructions: # 'start:' vacío: no hay nada
            return

        world.update_perceptions(creature)  # spec 2.7.2: snapshot
        ctx = EvalContext(creature, world, state)

        for _ in range(MAX_INSTRUCTIONS):
            instr = self._fetch(state)
            if self._execute(instr, ctx, state):
                return
        # Presupuesto agotado sin acción: el turno termina aquí.

    def _fetch(self, state):
        # Al llegar al final del archivo vuelve a 'start:' en el MISMO turno.
        if state.pc >= len(state.program.instructions):
            state.pc = state.program.labels.get("start", 0)
        return state.program.instructions[state.pc]

    def _execute(self, instr, ctx, state):
        handler = self._handlers.get(type(instr))
        if handler is None:
            raise RuntimeFault(
                f"instrucción desconocida: {instr!r}",
                line=getattr(instr, "line", None),
            )
        return handler(instr, ctx, state)

    # Manejadores: devuelven True si consumen el turno.

    def _do_goto(self, instr, ctx, state):
        state.pc = state.program.labels[instr.label]
        return False

    def _do_if(self, instr, ctx, state):
        if is_truthy(instr.condition.evaluate(ctx)):
            state.pc = state.program.labels[instr.label]
        else:
            state.pc += 1
        return False

    def _do_assign(self, instr, ctx, state):
        state.variables[instr.name] = instr.expr.evaluate(ctx)
        state.pc += 1
        return False

    def _do_call(self, instr, ctx, state):
        args = [arg.evaluate(ctx) for arg in instr.args]
        action = self.actions.get(instr.name)
        if action is None:
            raise RuntimeFault(
                f"acción desconocida '{instr.name}'", line=instr.line
            )
        consumes = action.execute(ctx, args, instr.line)
        state.pc += 1
        return consumes
