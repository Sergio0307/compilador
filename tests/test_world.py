# world/test_world.py
"""Tests del simulador: terreno, acciones, percepciones y rondas."""

from lang.compiler import compile_species
from lang.catalog import CONSTANTS

from world.world import World


def compilar(body="", **cabecera):
    """Compila un .ins de prueba con cabecera por defecto (fusiona kwargs)."""
    cab = {"creature": "Uruk", "faction": "isengard", "health": 10,
           "vision": 3, "lifespan": 100}
    cab.update(cabecera)
    src = "".join(f"{k} {v}\n" for k, v in cab.items()) + "start:\n" + body
    return compile_species(src, "t.ins")


# --------------------------------------------------------------------------
# Población y terreno
# --------------------------------------------------------------------------

def test_nacimiento():
    """add_creature y free_cells: la ocupada desaparece de las libres."""
    print("=== nacimiento ===")
    w = World(10, 10)
    c = w.add_creature(compilar(), 5, 5)
    assert (c.x, c.y) == (5, 5) and c.health == 10 and c.alive
    libres = w.free_cells()
    assert (5, 5) not in libres and (6, 5) in libres
    assert len(libres) == 99, len(libres)
    print("  OK, criatura nacida y casilla ocupada fuera de libres")
    print("=== nacimiento OK ===\n")


def test_move():
    """move se para en roca, en el borde y contra otra criatura."""
    print("=== move ===")
    w = World(10, 10)
    c = w.add_creature(compilar(), 5, 5)
    w.terrain.add_rock(7, 5)
    w.move(c, 1, 0, 5)
    assert (c.x, c.y) == (6, 5), (c.x, c.y)          # roca en 7,5
    w.move(c, -1, 0, 99)
    assert (c.x, c.y) == (0, 5), (c.x, c.y)          # borde: fuera es roca
    otra = w.add_creature(compilar(), 2, 5)
    w.move(c, 1, 0, 5)
    assert (c.x, c.y) == (1, 5), (c.x, c.y)          # otra criatura
    assert (otra.x, otra.y) == (2, 5)
    print("  OK, roca, borde y criatura detienen el avance")
    print("=== move OK ===\n")


# --------------------------------------------------------------------------
# Acciones de combate
# --------------------------------------------------------------------------

def test_attack():
    """attack daña, mata, falla al aire y en (0,0) golpea la casilla propia."""
    print("=== attack ===")
    w = World(10, 10)
    a = w.add_creature(compilar(), 5, 5)
    b = w.add_creature(compilar(creature="Orc", faction="mordor"), 6, 5)
    w.attack(a, 1, 0, 4)
    assert b.health == 6 and b.alive, b.health
    w.attack(a, 1, 0, 100)
    assert not b.alive and "ataque" in b.death_reason
    assert b.health == 0
    otro = w.add_creature(compilar(), 5, 7)
    w.attack(otro, 1, 0, 5)                          # golpe al aire
    assert otro.health == 10
    w.attack(a, 0, 0, 3)                             # (0,0) = su casilla
    assert a.health == 7, a.health
    print("  OK, daña, mata, falla al aire y (0,0) es la casilla propia")
    print("=== attack OK ===\n")


def test_consume():
    """consume daña como attack y cura al atacante con clamp a max."""
    print("=== consume ===")
    w = World(10, 10)
    a = w.add_creature(compilar(), 5, 5)
    b = w.add_creature(compilar(creature="Orc", faction="mordor"), 6, 5)
    a.health = 7
    w.consume(a, 1, 0, 4, 99)
    assert b.health == 6, b.health
    assert a.health == 10, a.health                  # clamp a max_health
    a.health = 7
    w.consume(a, 0, 1, 5, 1)                         # golpe al aire: solo cura
    assert a.health == 8, a.health
    print("  OK, daña al objetivo y cura con clamp")
    print("=== consume OK ===\n")


def test_reproduce():
    """reproduce: cría con health clamp, misma especie y Program compartido."""
    print("=== reproduce ===")
    w = World(10, 10)
    padre = w.add_creature(compilar(), 5, 5)
    w.reproduce(padre, 1, 0, 99)
    assert len(w.creatures) == 2, len(w.creatures)
    hijo = w.creature_at(6, 5)
    assert hijo is not None and hijo is not padre
    assert hijo.health == 10                          # clamp a max_health
    assert hijo.age == 0
    assert hijo.execution is not padre.execution
    assert hijo.execution.program is padre.execution.program  # mismo .ins
    w.reproduce(padre, 1, 0, 5)                       # casilla ocupada
    assert len(w.creatures) == 2, len(w.creatures)
    w.terrain.add_rock(5, 6)
    w.reproduce(padre, 0, 1, 5)                       # casilla de roca
    assert len(w.creatures) == 2, len(w.creatures)
    print("  OK, nace con clamp y no nace en casilla ocupada o roca")
    print("=== reproduce OK ===\n")


# --------------------------------------------------------------------------
# Rondas: edad, vejez, ictus
# --------------------------------------------------------------------------

def test_vejez():
    """age +1 por ronda; al llegar a lifespan muere de vejez."""
    print("=== vejez ===")
    w = World(10, 10)
    c = w.add_creature(compilar(lifespan=2), 5, 5)
    w.run_round()
    assert c.alive and c.age == 1, c.age
    w.run_round()
    assert not c.alive and c.death_reason == "vejez"
    assert c.age == 2, c.age
    print("  OK, vive lifespan rondas y muere de vejez")
    print("=== vejez OK ===\n")


def test_ictus():
    """Un RuntimeFault mata al bicho con reason 'ictus' y va al log."""
    print("=== ictus ===")
    w = World(10, 10)
    c = w.add_creature(compilar("z = 1 / 0\n"), 5, 5)
    w.run_round()
    assert not c.alive, "debía morir de ictus"
    assert "ictus" in c.death_reason and "cero" in c.death_reason
    assert any(e[0] == "muerte" for e in w.log), w.log
    print("  OK:", c.death_reason)
    print("=== ictus OK ===\n")


def test_e2e_rondas():
    """Especie que camina al este cada ronda y muere a los 3 ticks."""
    print("=== e2e en rondas ===")
    w = World(10, 10, seed=1)
    c = w.add_creature(compilar("move(1, 0, 1)\ngoto start\n", lifespan=3), 0, 0)
    w.run_round()
    assert (c.x, c.y) == (1, 0) and c.age == 1, (c.x, c.age)
    w.run_round()
    assert (c.x, c.y) == (2, 0)
    w.run_round()
    assert (c.x, c.y) == (3, 0) and not c.alive
    assert c.death_reason == "vejez"
    assert w.run_round() == []                       # mundo vacío
    assert w.tick == 4, w.tick
    print("  OK, caminó 3 casillas, murió de vejez y el mundo quedó vacío")
    print("=== e2e en rondas OK ===\n")


def test_log_say():
    """say no toca el mundo pero queda en el log con su tick."""
    print("=== log de say ===")
    w = World(10, 10)
    w.add_creature(compilar('say("hola")\nwait(1)\n'), 5, 5)
    w.run_round()
    assert ("dice", 0, "Uruk", "hola") in w.log, w.log
    print("  OK:", ("dice", 0, "Uruk", "hola"))
    print("=== log de say OK ===\n")


# --------------------------------------------------------------------------
# Percepciones
# --------------------------------------------------------------------------

def test_percepciones():
    """El snapshot rellena yo/mundo y se congela hasta el siguiente turno."""
    print("=== percepciones ===")
    w = World(10, 10, seed=42)
    a = w.add_creature(compilar(vision=2), 5, 5)
    w.add_creature(compilar(), 9, 9)                              # aliada
    w.add_creature(compilar(creature="Orc", faction="mordor"), 6, 5)
    w.terrain.set_reserve(5, 5, 7)
    w.update_perceptions(a)
    p = a.perceptions
    assert p["health"] == 10 and p["age"] == 0 and p["lifespan"] == 100
    assert p["species"] == "Uruk" and p["faction"] == "isengard"
    assert (p["x"], p["y"]) == (5, 5) and p["vision"] == 2
    assert p["terrain_here"] == 0 and p["reserve_here"] == 7
    assert p["width"] == 10 and p["height"] == 10 and p["tick"] == 0
    assert p["total_creatures"] == 3
    assert p["total_allies"] == 1 and p["total_enemies"] == 1  # excluye a 'a'
    assert 0 <= p["random"] <= 99, p["random"]
    a.health = 4
    assert w.perception(a, "health") == 10        # congelado hasta el turno
    print("  OK, snapshot completo y congelado")
    print("=== percepciones OK ===\n")


def test_near():
    """Conteos y dist/dx/dy en el radio; -1/0/0 cuando no hay nadie."""
    print("=== percepciones cerca ===")
    w = World(10, 10)
    a = w.add_creature(compilar(vision=3), 5, 5)
    w.add_creature(compilar(creature="Orc", faction="mordor"), 8, 5)   # dist 3
    w.add_creature(compilar(creature="Orc2", faction="mordor"), 5, 9)  # dist 4
    w.terrain.add_rock(6, 6)
    w.update_perceptions(a)
    p = a.perceptions
    assert p["enemies_near"] == 1, p["enemies_near"]      # el de dist 4 no cuenta
    assert (p["enemy_dist"], p["enemy_dx"], p["enemy_dy"]) == (3, 1, 0)
    assert p["objects_near"] == 1, p["objects_near"]
    assert (p["object_dist"], p["object_dx"], p["object_dy"]) == (1, 1, 1)
    assert p["allies_near"] == 0
    assert (p["ally_dist"], p["ally_dx"], p["ally_dy"]) == (-1, 0, 0)

    solo = World(10, 10)
    bicho = solo.add_creature(compilar(vision=3), 5, 5)
    solo.update_perceptions(bicho)
    assert solo.perception(bicho, "enemy_dist") == -1
    assert solo.perception(bicho, "object_dist") == -1
    assert solo.perception(bicho, "enemies_near") == 0
    assert solo.perception(bicho, "objects_near") == 0
    print("  OK, radio cuadrado y ausentes con dist -1")
    print("=== percepciones cerca OK ===\n")


# --------------------------------------------------------------------------
# see / name / roar
# --------------------------------------------------------------------------

def test_see_nombre():
    """see/name con coords absolutas, prioridad y el borde como roca."""
    print("=== see y name ===")
    w = World(10, 10)
    a = w.add_creature(compilar(vision=3), 5, 5)
    w.add_creature(compilar(), 4, 5)                            # aliada
    w.add_creature(compilar(creature="Orc", faction="mordor"), 7, 5)
    w.terrain.add_rock(6, 7)
    assert w.see(a, 4, 5) == CONSTANTS["ALLY"]
    assert w.see(a, 7, 5) == CONSTANTS["ENEMY"]
    assert w.see(a, 6, 7) == CONSTANTS["OBJECT"]   # Chebyshev 2 <= 3
    assert w.see(a, 5, 6) == CONSTANTS["GROUND"]
    assert w.see(a, 5, 5) == CONSTANTS["GROUND"]   # la casilla propia: suelo
    assert w.name_at(a, 7, 5) == "Orc"
    assert w.name_at(a, 6, 7) == "Rock"
    assert w.name_at(a, 5, 6) == ""
    assert w.see(a, 5, 9) == CONSTANTS["NONE"]     # dist 4 > vision 3
    assert w.name_at(a, 5, 9) == ""
    borde = w.add_creature(compilar(vision=3), 1, 5)
    assert w.see(borde, -1, 5) == CONSTANTS["OBJECT"]  # fuera = roca
    assert w.name_at(borde, -1, 5) == "Rock"
    print("  OK, ALLY/ENEMY/OBJECT/GROUND, radio y borde-roca")
    print("=== see y name OK ===\n")


def test_roar():
    """Roar lo oyen quienes están en el radio; caduca a los 3 ticks."""
    print("=== roar ===")
    w = World(10, 10)
    a = w.add_creature(compilar(vision=3), 5, 5)
    oido = w.add_creature(compilar(), 7, 5)        # dist 2: oye
    lejos = w.add_creature(compilar(), 9, 9)       # dist 4: no oye
    w.roar(a, 7)
    w.update_perceptions(oido)
    assert w.perception(oido, "roars_near") == 1
    assert w.perception(oido, "last_roar") == 7
    w.update_perceptions(lejos)
    assert w.perception(lejos, "roars_near") == 0
    assert w.perception(lejos, "last_roar") == ""
    for _ in range(3):                             # 3 ticks: caduca
        w.run_round()
    w.update_perceptions(oido)
    assert w.perception(oido, "roars_near") == 0
    print("  OK, oído en el radio, no fuera, caduca a los 3 ticks")
    print("=== roar OK ===\n")


def main():
    test_nacimiento()
    test_move()
    test_attack()
    test_consume()
    test_reproduce()
    test_vejez()
    test_ictus()
    test_e2e_rondas()
    test_log_say()
    test_percepciones()
    test_near()
    test_see_nombre()
    test_roar()
    print("TODOS LOS TESTS DEL MUNDO OK")


if __name__ == "__main__":
    main()
