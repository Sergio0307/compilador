"""Criatura viva del mundo: estado físico + su ejecución del lenguaje.

La criatura no interpreta nada por sí sola: `execution` es el estado que
usa lang.interpreter. El mundo rellena `perceptions` (el snapshot del
turno) y actualiza `health`, `age` y la posición cuando corre las acciones.
"""


class Creature:
    def __init__(self, species_def, execution, x, y):
        self.species_def = species_def      # SpeciesDef: para reproducirse
        self.species = species_def.name     # percepción 'species'
        self.faction = species_def.faction
        self.max_health = species_def.health
        self.health = species_def.health
        self.vision = species_def.vision
        self.lifespan = species_def.lifespan
        self.age = 0
        self.x = x
        self.y = y
        self.execution = execution
        self.alive = True
        self.death_reason = ""
        self.perceptions = {}               # snapshot del turno (spec 2.7.2)

    def kill(self, reason):
        """La mata (ictus, daño o vejez). Idempotente."""
        if self.alive:
            self.alive = False
            self.death_reason = reason
