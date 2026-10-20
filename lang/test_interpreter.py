# lang/test_interpreter.py
"""Tests del intérprete contra un mundo falso (FakeWorld).

FakeWorld solo cumple la interfaz que el intérprete espera del mundo: no
simula nada, únicamente registra las llamadas y devuelve valores
programados. Así se prueba el intérprete en aislamiento, sin depender de
world/ (que aún no existe).
"""

from lang.compiler import compile_species
from lang.interpreter import Interpreter, Program, CreatureExecution
from lang.errors import RuntimeFault
from lang.actions import ACTION_BY_NAME
from lang.catalog import ACTIONS, CONSTANTS


HEADER = ["creature X", "faction f", "health 10", "vision 3", "lifespan 100"]


class FakeCreature:
    """Lo único que el intérprete pide a la criatura es su execution."""

    def __init__(self):
        self.execution = None


class FakeWorld:
    """Cumple la interfaz que el intérprete espera del mundo: no simula
    nada, únicamente registra las llamadas y devuelve valores programados."""

    def __init__(self):
        self.calls = []          # [accion, ...] registradas
        self.perceptions = {}    # nombre -> valor del snapshot
        self.see_values = {}     # (x, y) -> valor de see()
        self.name_values = {}    # (x, y) -> texto de name()
        self.update_count = 0    # veces que se hizo el snapshot

    def update_perceptions(self, creature):
        self.update_count += 1

    def perception(self, creature, name):
        return self.perceptions.get(name, 0)

    def see(self, creature, x, y):
        self.calls.append(("see", x, y))
        return self.see_values.get((x, y), 0)

    def name_at(self, creature, x, y):
        self.calls.append(("name", x, y))
        return self.name_values.get((x, y), "")

    def move(self, creature, dx, dy, speed):
        self.calls.append(("move", dx, dy, speed))

    def attack(self, creature, dx, dy, damage):
        self.calls.append(("attack", dx, dy, damage))

    def consume(self, creature, dx, dy, damage, heal):
        self.calls.append(("consume", dx, dy, damage, heal))

    def reproduce(self, creature, dx, dy, health):
        self.calls.append(("reproduce", dx, dy, health))

    def roar(self, creature, value):
        self.calls.append(("roar", value))

    def say(self, creature, value):
        self.calls.append(("say", value))


def make_creature(body):
    """Compila 'cabecera + cuerpo' y devuelve (criatura, estado)."""
    src = "".join(line + "\n" for line in HEADER) + "start:\n" + body
    species = compile_species(src, "t.ins")
    creature = FakeCreature()
    execution = CreatureExecution(Program.from_species(species))
    creature.execution = execution
    return creature, execution


def run_turns(body, turns=1, world=None):
    """Corre N turnos y devuelve (criatura, estado, mundo falso)."""
    creature, execution = make_creature(body)
    world = world or FakeWorld()
    interp = Interpreter()
    for _ in range(turns):
        interp.run_turn(creature, world)
    return creature, execution, world


def expect_fault(body, fragment):
    """Un turno con `body` debe lanzar RuntimeFault con `fragment` y línea."""
    creature, _ = make_creature(body)
    world = FakeWorld()
    try:
        Interpreter().run_turn(creature, world)
    except RuntimeFault as e:
        assert fragment in str(e), f"esperaba {fragment!r} en: {e}"
        assert e.line is not None, "el error no trae línea"
        print("  OK:", e)
        return e
    raise AssertionError("debía lanzar RuntimeFault")


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_registro_acciones():
    """Las 7 acciones del catálogo tienen su clase registrada."""
    print("=== registro de acciones ===")
    assert len(ACTIONS) == 7 and len(ACTION_BY_NAME) == 7
    for name, arity in ACTIONS.items():
        assert name in ACTION_BY_NAME, name
        assert ACTION_BY_NAME[name].arity == arity, name
    print("  OK, 7 acciones registradas con su aridad")
    print("=== registro de acciones OK ===\n")


def test_turno_accion():
    """Una acción consume el turno; el pc avanza a la instrucción siguiente."""
    print("=== turno con acción ===")
    _, execution, world = run_turns("move(1, 0, 2)\ngoto start\n")
    assert world.calls == [("move", 1, 0, 2)], world.calls  # el goto no corrió
    assert world.update_count == 1, world.update_count
    assert execution.pc == 1, execution.pc
    print("  OK, move aplicado y percepciones actualizadas una vez")
    print("=== turno con acción OK ===\n")


def test_say_no_consume():
    """say es la única acción que no consume turno: sigue hasta la acción."""
    print("=== say no consume ===")
    _, _, world = run_turns('say("hi")\nmove(1, 0, 1)\n')
    assert world.calls == [("say", "hi"), ("move", 1, 0, 1)], world.calls
    print("  OK, say y move en el mismo turno")
    print("=== say no consume OK ===\n")


def test_wait():
    """wait(n): el turno actual + n-1 turnos dormidos (n=3 -> 2, 1, 0)."""
    print("=== wait ===")
    creature, execution = make_creature("wait(3)\n")
    world = FakeWorld()
    interp = Interpreter()
    dormidos = []
    for _ in range(3):
        interp.run_turn(creature, world)
        dormidos.append(execution.waiting)
    assert dormidos == [2, 1, 0], dormidos
    # dormir no gasta snapshot: solo el primer turno actualizó percepciones
    assert world.update_count == 1, world.update_count
    # el cuarto turno despierta y vuelve a ejecutar wait
    interp.run_turn(creature, world)
    assert execution.waiting == 2, execution.waiting
    assert world.update_count == 2, world.update_count
    print("  OK, sueño 2 -> 1 -> 0, despierta en el 4º sin gastar snapshot")
    print("=== wait OK ===\n")


def test_presupuesto_100():
    """Sin acción, el turno corta a las 100 líneas."""
    print("=== tope de 100 líneas ===")
    _, execution, world = run_turns("n = 0\nloop:\nn = n + 1\ngoto loop\n")
    assert execution.variables["n"] == 50, execution.variables
    assert world.update_count == 1, world.update_count
    print("  OK, cortó a las 100 líneas (n = 50)")
    print("=== tope de 100 líneas OK ===\n")


def test_wrap_mismo_turno():
    """Al llegar al final del archivo vuelve a start en el MISMO turno."""
    print("=== wrap en el mismo turno ===")
    _, _, world = run_turns('say("a")\n')
    says = sum(1 for c in world.calls if c == ("say", "a"))
    assert says == 100, says
    print(f"  OK, envolvió a start y ejecutó hasta el tope ({says} says)")
    print("=== wrap en el mismo turno OK ===\n")


def test_memoria_entre_turnos():
    """Las variables propias persisten: el turno 2 lee lo que dejó el 1."""
    print("=== memoria entre turnos ===")
    body = ("count = 0\n"
            "loop:\n"
            "count = count + 1\n"
            "if count < 3 goto loop\n"
            "wait(1)\n"
            "after:\n"
            "say(count)\n")
    _, execution, world = run_turns(body, turns=2)
    assert execution.variables["count"] == 3, execution.variables
    # el turno 1 espera con count=3; el 2 retoma en 'say(count)' sin resetear
    assert ("say", 3) in world.calls, world.calls
    print("  OK, contó hasta 3 y el turno 2 leyó el valor del turno 1")
    print("=== memoria entre turnos OK ===\n")


def test_see_constantes():
    """see() y las constantes (GROUND) se resuelven y comparan bien."""
    print("=== see y constantes ===")
    world = FakeWorld()
    world.see_values[(1, 0)] = CONSTANTS["GROUND"]
    _, _, world = run_turns(
        'if see(1, 0) == GROUND goto win\nsay("perdi")\nwin:\nwait(1)\n',
        world=world,
    )
    assert ("see", 1, 0) in world.calls, world.calls
    assert not any(c == ("say", "perdi") for c in world.calls), "no saltó"
    print("  OK, see(resp) == GROUND -> saltó a win")
    print("=== see y constantes OK ===\n")


def test_name_funcion():
    """name() se resuelve dentro de una expresión y compara texto."""
    print("=== función name ===")
    world = FakeWorld()
    world.name_values[(1, 2)] = "Rock"
    _, _, world = run_turns(
        'if name(1, 2) == "Rock" goto hit\nsay("rock")\nhit:\nwait(1)\n',
        world=world,
    )
    assert ("name", 1, 2) in world.calls, world.calls
    assert not any(c == ("say", "rock") for c in world.calls), "no saltó"
    print("  OK, name() llamada y comparada")
    print("=== función name OK ===\n")


def test_percepcion():
    """Las percepciones se leen desde el snapshot del mundo."""
    print("=== percepción ===")
    world = FakeWorld()
    world.perceptions["health"] = 5
    _, _, world = run_turns(
        "if health < 10 goto low\nwait(1)\nlow:\nmove(1, 0, 1)\n",
        world=world,
    )
    assert ("move", 1, 0, 1) in world.calls, world.calls
    print("  OK, health=5 -> saltó a low y ejecutó move")
    print("=== percepción OK ===\n")


def test_resto_acciones():
    """attack, consume y reproduce aplican con sus direcciones."""
    print("=== attack / consume / reproduce ===")
    _, _, world = run_turns(
        "attack(1, -1, 5)\nconsume(0, 0, 3, 4)\nreproduce(-1, 0, 20)\n",
        turns=3,
    )
    for esperado in (("attack", 1, -1, 5),
                     ("consume", 0, 0, 3, 4),
                     ("reproduce", -1, 0, 20)):
        assert esperado in world.calls, (esperado, world.calls)
    print("  OK:", [c for c in world.calls if c[0] != "see"])
    print("=== attack / consume / reproduce OK ===\n")


def test_roar_say_aceptan_numeros():
    """roar y say aceptan cualquier valor, incluidos números."""
    print("=== roar/say con números ===")
    _, _, world = run_turns("say(7)\nroar(42)\n")
    assert ("say", 7) in world.calls, world.calls
    assert ("roar", 42) in world.calls, world.calls
    print("  OK, say(7) y roar(42)")
    print("=== roar/say con números OK ===\n")


def test_truthiness_logica():
    """and/or/not normalizan a 0/1 con la noción de verdad."""
    print("=== lógica ===")
    _, execution, world = run_turns(
        'if 0 or "" goto wrong\nflag = 1 and 5\nflag2 = not 1\n'
        'wait(1)\nwrong:\nsay("mal")\n'
    )
    assert execution.variables["flag"] == 1, execution.variables
    assert execution.variables["flag2"] == 0, execution.variables
    assert not any(c == ("say", "mal") for c in world.calls), "no saltó"
    print("  OK, 0 or \"\" es falso, 1 and 5 es 1 y not 1 es 0")
    print("=== lógica OK ===\n")


def test_errores_runtime():
    """Los errores de ejecución lanzan RuntimeFault con su fragmento."""
    print("=== errores en tiempo de ejecución ===")
    casos = [
        ("z = 1 / 0\n",              "división por cero"),
        ("if foo > 0 goto start\n",  "antes de asignarse"),
        ("move(2, 0, 1)\n",          "dirección fuera de rango"),
        ('z = 1 + "a"\n',            "'+' a número y texto"),
        ('move("a", 0, 1)\n',        "se esperaba un número"),
        ('if 1 == "a" goto start\n', "'==' a número y texto"),
    ]
    for body, fragment in casos:
        expect_fault(body, fragment)
    print("=== errores en tiempo de ejecución OK ===\n")


def test_error_con_linea():
    """El error de ejecución reporta la línea del código."""
    print("=== línea del error ===")
    e = expect_fault("z = 1 / 0\n", "división por cero")
    assert e.line == 7, e.line  # 5 de cabecera + 'start:' + la división
    print("  OK, línea reportada:", e.line)
    print("=== línea del error OK ===\n")


def test_programa_vacio():
    """'start:' sin instrucciones: el guard corta el turno sin crashear."""
    print("=== programa vacío ===")
    creature, execution = make_creature("")
    world = FakeWorld()
    Interpreter().run_turn(creature, world)
    assert world.update_count == 0, world.update_count  # sale antes del snapshot
    assert execution.pc == 0, execution.pc
    print("  OK, no crashea y no gasta turno")
    print("=== programa vacío OK ===\n")


def main():
    test_registro_acciones()
    test_turno_accion()
    test_say_no_consume()
    test_wait()
    test_presupuesto_100()
    test_wrap_mismo_turno()
    test_memoria_entre_turnos()
    test_see_constantes()
    test_name_funcion()
    test_percepcion()
    test_resto_acciones()
    test_roar_say_aceptan_numeros()
    test_truthiness_logica()
    test_errores_runtime()
    test_error_con_linea()
    test_programa_vacio()
    print("TODOS LOS TESTS DEL INTÉRPRETE OK")


if __name__ == "__main__":
    main()
