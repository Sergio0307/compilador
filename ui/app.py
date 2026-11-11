from pathlib import Path

import pygame

from loaders.resource_manager import ResourceManager
from ui.map import MapView
from world.world import World


class InstinctApp:
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 60

    BACKGROUND = (18, 23, 26)
    PANEL = (28, 36, 40)
    TEXT = (226, 232, 234)
    MUTED = (148, 163, 168)
    ACCENT = (214, 168, 74)
    ERROR = (232, 104, 104)
    MAP_RECT = pygame.Rect(1020, 300, 780, 350)
    START_BUTTON = pygame.Rect(110, 780, 220, 48)
    RESTART_BUTTON = pygame.Rect(1710, 162, 150, 40)
    LOG_RECT = pygame.Rect(100, 468, 820, 292)
    SPEEDS = (2, 10, 30)
    SPEED_BUTTONS = (
        pygame.Rect(610, 786, 64, 36),
        pygame.Rect(682, 786, 72, 36),
        pygame.Rect(762, 786, 72, 36),
    )

    def __init__(self, content_root=None):
        pygame.font.init()

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("Instinct | Dota Battlefield")

        self.clock = pygame.time.Clock()
        self.running = True
        self.phase = "preparation"

        self.title_font = pygame.font.Font(None, 72)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        root = (
            Path(content_root)
            if content_root
            else Path(__file__).resolve().parent.parent
        )
        self.manager = ResourceManager(root)
        self.load_errors = self.manager.load_all()
        self.selected_map_index = 0
        self.selected_species_index = 0
        self.map_view = MapView()
        self.world_map = None
        self.world = None
        self.selected_creature = None
        self.status = ""
        self.status_is_error = False
        self.paused = False
        self.speed_index = 0
        self.ticks_per_second = self.SPEEDS[0]
        self.tick_accumulator = 0.0
        self.rebuild_map()

        for error in self.load_errors:
            print(f"aviso: {error}")

    @property
    def map_names(self):
        return list(self.manager.maps)

    @property
    def selected_map(self):
        maps = list(self.manager.maps.values())
        if not maps:
            return None
        return maps[self.selected_map_index % len(maps)]

    @property
    def selected_species(self):
        species = list(self.manager.creatures.values())
        if not species:
            return None
        return species[self.selected_species_index % len(species)]

    def rebuild_map(self):
        self.phase = "preparation"
        self.paused = False
        self.selected_creature = None
        self.speed_index = 0
        self.ticks_per_second = self.SPEEDS[0]
        self.tick_accumulator = 0.0
        selected = self.selected_map
        if selected is None:
            self.world_map = None
            self.world = None
            return

        self.world_map = selected.build()
        self.world = World(self.world_map)

    def set_speed(self, index):
        if self.phase != "playing" or not 0 <= index < len(self.SPEEDS):
            return

        self.speed_index = index
        self.ticks_per_second = self.SPEEDS[index]
        self.tick_accumulator = 0.0
        self.set_status(f"Velocidad: {self.ticks_per_second} ticks/s.")

    def restart_game(self):
        if self.phase != "playing":
            return

        self.rebuild_map()
        self.set_status("Partida reiniciada. Elige criaturas y pulsa Empezar.")

    def place_creature(self, position):
        if self.phase != "preparation":
            self.set_status("La partida ya empezó.", error=True)
            return
        world = self.world
        world_map = self.world_map
        if world is None or world_map is None:
            self.set_status("No hay un mapa cargado.", error=True)
            return

        species = self.selected_species
        if species is None:
            self.set_status("No hay criaturas cargadas.", error=True)
            return

        cell = self.map_view.screen_to_cell(position, world_map, self.MAP_RECT)
        if cell is None:
            return

        try:
            creature = world.add_creature(species, cell[0], cell[1])
        except ValueError as exc:
            self.set_status(str(exc), error=True)
        else:
            self.set_status(f"{creature.species} colocado en ({cell[0]}, {cell[1]})")

    def remove_creature(self, position):
        if self.phase != "preparation":
            self.set_status("La partida ya empezó.", error=True)
            return
        world = self.world
        world_map = self.world_map
        if world is None or world_map is None:
            self.set_status("No hay un mapa cargado.", error=True)
            return

        cell = self.map_view.screen_to_cell(position, world_map, self.MAP_RECT)
        if cell is None:
            return

        creature = world.creature_at(cell[0], cell[1])
        if creature is None:
            self.set_status(
                f"No hay una criatura en ({cell[0]}, {cell[1]}).",
                error=True,
            )
            return

        species = creature.species
        world.remove_creature(creature)
        self.set_status(f"{species} eliminado de ({cell[0]}, {cell[1]})")

    def inspect_cell(self, position):
        if self.phase != "playing":
            return
        world = self.world
        world_map = self.world_map
        if world is None or world_map is None:
            return

        cell = self.map_view.screen_to_cell(position, world_map, self.MAP_RECT)
        if cell is None:
            self.selected_creature = None
            return

        creature = world.creature_at(cell[0], cell[1])
        if creature is None:
            self.selected_creature = None
            self.set_status(f"Casilla ({cell[0]}, {cell[1]}) sin criatura.")
            return

        if creature is self.selected_creature:
            self.selected_creature = None
            self.set_status("Selección quitada.")
            return

        self.selected_creature = creature
        self.set_status(f"Inspeccionando {creature.species} en ({cell[0]}, {cell[1]}).")

    def start_game(self):
        if self.phase != "preparation":
            return
        world = self.world
        world_map = self.world_map
        if world is None or world_map is None:
            self.set_status("No hay un mapa cargado.", error=True)
            return
        if not world.creatures:
            self.set_status(
                "Coloca al menos una criatura antes de empezar.", error=True
            )
            return

        self.phase = "playing"
        self.paused = False
        self.tick_accumulator = 0.0
        self.set_status(
            f"Partida iniciada en {world_map.name}. "
            f"Corre a {self.ticks_per_second} ticks/s, P pausa."
        )

    def advance_tick(self):
        world = self.world
        if self.phase != "playing" or world is None:
            return

        alive = world.run_round()
        if self.selected_creature is not None and not self.selected_creature.alive:
            self.selected_creature = None
        self.set_status(f"Tick {world.tick}: {len(alive)} criaturas vivas.")

    def toggle_pause(self):
        if self.phase != "playing":
            return

        self.paused = not self.paused
        self.tick_accumulator = 0.0
        if self.paused:
            self.set_status("En pausa. Espacio avanza un tick, P sigue.")
        else:
            self.set_status("Corriendo de nuevo.")

    def step_once(self):
        if self.phase != "playing":
            return

        self.paused = True
        self.tick_accumulator = 0.0
        self.advance_tick()
        self.set_status(self.status + " (pausa)")

    def set_status(self, message, error=False):
        self.status = message
        self.status_is_error = error

    @staticmethod
    def format_log_entry(entry):
        kind, tick, name, value = entry
        if kind == "carga":
            return f"carga: {value}".replace("\n", " ")
        if kind == "dice":
            body = f"{name} dice: {value}"
        elif kind == "rugido":
            body = f"{name} ruge: {value}"
        elif kind == "muerte":
            body = f"{name} muere ({value})"
        elif kind == "nacimiento":
            body = f"{name} nace en {value}"
        else:
            body = f"{kind}: {name} {value}"
        return f"[t{tick}] {body}".replace("\n", " ")

    def clipped(self, font, text, max_width):
        if font.size(text)[0] <= max_width:
            return text

        while text and font.size(text + "…")[0] > max_width:
            text = text[:-1]
        return text + "…"

    def log_color(self, kind):
        return {
            "carga": self.ERROR,
            "muerte": self.ERROR,
            "nacimiento": (122, 190, 140),
            "rugido": self.ACCENT,
            "dice": (150, 180, 200),
        }.get(kind, self.MUTED)

    def draw_log(self, top):
        top = max(self.LOG_RECT.top, min(top, self.LOG_RECT.bottom))
        height = self.LOG_RECT.bottom - top
        if height < 70:
            return

        rect = pygame.Rect(self.LOG_RECT.left, top, self.LOG_RECT.width, height)
        pygame.draw.rect(self.screen, (24, 31, 35), rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            (56, 68, 74),
            rect,
            width=1,
            border_radius=8,
        )
        max_lines = max(1, (height - 52) // 24)
        title = "Registro"
        if self.load_errors:
            title = f"Registro · carga: {len(self.load_errors)}"
        self.text(self.body_font, title, 115, top + 10, self.TEXT)

        load_entries = [
            ("carga", 0, "", str(error)) for error in self.load_errors
        ]
        runtime_entries = self.world.log if self.world is not None else []
        if len(load_entries) >= max_lines:
            entries = load_entries[:max_lines]
        elif load_entries:
            room = max_lines - len(load_entries)
            entries = load_entries + runtime_entries[-room:]
        else:
            entries = runtime_entries[-max_lines:]
        if not entries:
            self.text(
                self.small_font,
                "Sin eventos todavía.",
                120,
                top + 44,
                self.MUTED,
            )
            return

        y = top + 44
        for entry in entries:
            line = self.clipped(
                self.small_font,
                self.format_log_entry(entry),
                rect.width - 30,
            )
            self.text(
                self.small_font,
                line,
                120,
                y,
                self.log_color(entry[0]),
            )
            y += 24

    def health_color(self, creature):
        ratio = max(0.0, min(1.0, creature.health / creature.max_health))
        if ratio >= 0.6:
            return (94, 200, 112)
        if ratio >= 0.3:
            return (230, 190, 70)
        return self.ERROR

    @staticmethod
    def current_label(execution):
        best = "?"
        best_index = -1
        for name, index in execution.program.labels.items():
            if index <= execution.pc and index > best_index:
                best = name
                best_index = index
        return best

    @staticmethod
    def current_line(execution):
        program = execution.program
        if 0 <= execution.pc < len(program.instructions):
            return getattr(program.instructions[execution.pc], "line", None)
        return None

    @staticmethod
    def format_variables(variables):
        if not variables:
            return "(ninguna)"
        items = list(variables.items())
        parts = [f"{name}={value}" for name, value in items[:3]]
        if len(items) > 3:
            parts.append("…")
        return "   ".join(parts)

    @staticmethod
    def format_perceptions(perceptions):
        if not perceptions:
            return "(sin turno)"
        keys = ("enemy_dist", "enemies_near", "reserve_here")
        return "   ".join(
            f"{key}={perceptions.get(key, '?')}" for key in keys
        )

    def draw_inspector(self):
        self.text(self.heading_font, "Criatura", 1010, 660, self.TEXT)

        creature = self.selected_creature
        if creature is None:
            self.text(
                self.small_font,
                "Haz clic en una criatura para ver sus datos.",
                1020,
                705,
                self.MUTED,
            )
            return

        world_map = self.world_map
        terrain_name = "?"
        if world_map is not None:
            terrain = world_map.terrain_at(creature.x, creature.y)
            if terrain is not None:
                terrain_name = terrain.name

        execution = creature.execution
        line = self.current_line(execution)
        line_text = "—" if line is None else str(line)
        label_name = self.current_label(execution)

        rows = [
            ("Especie", f"{creature.species}  ·  {creature.faction}", self.TEXT),
            (
                "Salud",
                f"{creature.health} / {creature.max_health}   "
                f"Edad: {creature.age} / {creature.lifespan}",
                self.health_color(creature),
            ),
            (
                "Posición",
                f"({creature.x}, {creature.y})   Terreno: {terrain_name}",
                self.TEXT,
            ),
            ("Línea", f"{line_text}   {label_name}", self.TEXT),
            ("Variables", self.format_variables(execution.variables), self.TEXT),
            ("Percibe", self.format_perceptions(creature.perceptions), self.TEXT),
        ]
        y = 700
        for label, value, color in rows:
            self.text(self.small_font, f"{label}:", 1020, y, self.MUTED)
            value = self.clipped(self.small_font, value, 690)
            self.text(self.small_font, value, 1120, y, color)
            y += 24

    def draw_errors(self):
        self.text(self.heading_font, "Errores de carga", 1010, 680, self.TEXT)
        y = 720
        if self.load_errors:
            for error in self.load_errors[:4]:
                self.text(self.small_font, str(error)[:110], 1020, y, self.ERROR)
                y += 24
            remaining = len(self.load_errors) - 4
            if remaining > 0:
                self.text(
                    self.small_font,
                    f"... y {remaining} más en Registro.",
                    1020,
                    y,
                    self.MUTED,
                )
        else:
            self.text(self.body_font, "Sin errores.", 1020, y, self.MUTED)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif self.phase == "preparation":
                if event.key in (pygame.K_UP, pygame.K_DOWN) and self.manager.maps:
                    step = -1 if event.key == pygame.K_UP else 1
                    self.selected_map_index = (self.selected_map_index + step) % len(
                        self.manager.maps
                    )
                    self.rebuild_map()
                    self.set_status("")
                elif (
                    event.key in (pygame.K_LEFT, pygame.K_RIGHT)
                    and self.manager.creatures
                ):
                    step = -1 if event.key == pygame.K_LEFT else 1
                    self.selected_species_index = (
                        self.selected_species_index + step
                    ) % len(self.manager.creatures)
                    self.set_status("")
            elif self.phase == "playing":
                if event.key == pygame.K_SPACE:
                    self.step_once()
                elif event.key == pygame.K_p:
                    self.toggle_pause()
                elif event.key == pygame.K_r:
                    self.restart_game()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.set_speed(
                        (pygame.K_1, pygame.K_2, pygame.K_3).index(event.key)
                    )
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.phase == "playing" and self.RESTART_BUTTON.collidepoint(
                    event.pos
                ):
                    self.restart_game()
                elif self.START_BUTTON.collidepoint(event.pos):
                    if self.phase == "preparation":
                        self.start_game()
                    elif self.phase == "playing":
                        self.toggle_pause()
                elif self.phase == "playing":
                    for index, rect in enumerate(self.SPEED_BUTTONS):
                        if rect.collidepoint(event.pos):
                            self.set_speed(index)
                            break
                    else:
                        self.inspect_cell(event.pos)
                else:
                    self.place_creature(event.pos)
            elif event.button == 3:
                self.remove_creature(event.pos)

    def update(self, dt):
        if self.phase != "playing" or self.paused or self.world is None:
            return

        interval = 1.0 / self.ticks_per_second
        self.tick_accumulator += dt
        ticks = 0
        while self.tick_accumulator >= interval and ticks < 5:
            self.tick_accumulator -= interval
            self.advance_tick()
            ticks += 1
        if ticks == 5:
            self.tick_accumulator = 0.0

    def text(self, font, text, x, y, color=None):
        surface = font.render(text, True, color or self.TEXT)
        self.screen.blit(surface, (x, y))

    def draw(self):
        self.screen.fill(self.BACKGROUND)

        self.text(self.title_font, "INSTINCT", 80, 60, self.ACCENT)
        tagline = (
            "Preparación — contenido cargado desde terrains/, objects/, maps/ y creatures/"
            if self.phase == "preparation"
            else "Simulación — el mundo avanza solo (P pausa)"
        )
        self.text(
            self.body_font,
            tagline,
            80,
            145,
            self.MUTED,
        )

        selected = self.selected_map
        if selected is not None:
            self.text(
                self.body_font,
                f"Mapa seleccionado: {selected.name} "
                f"({selected.width} x {selected.height})",
                80,
                180,
                self.ACCENT,
            )
        else:
            self.text(self.body_font, "No hay mapas cargados.", 80, 180, self.ERROR)

        phase_label = "Preparación"
        if self.phase == "playing":
            state = "pausa" if self.paused else "corriendo"
            phase_label = (
                f"En juego — tick {self.world.tick if self.world else 0} — {state}"
            )
        self.text(self.body_font, phase_label, 700, 180, self.ACCENT)

        if self.phase == "playing":
            pygame.draw.rect(
                self.screen, (42, 52, 57), self.RESTART_BUTTON, border_radius=8
            )
            pygame.draw.rect(
                self.screen,
                self.ACCENT,
                self.RESTART_BUTTON,
                width=1,
                border_radius=8,
            )
            restart_label = self.small_font.render("Reiniciar (R)", True, self.TEXT)
            self.screen.blit(
                restart_label,
                restart_label.get_rect(center=self.RESTART_BUTTON.center),
            )

        panel = pygame.Rect(80, 210, 860, 640)
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.ACCENT, panel, width=2, border_radius=10)

        self.text(self.heading_font, "Mapas", 110, 235, self.TEXT)
        y = 285
        if self.manager.maps:
            for index, map_def in enumerate(self.manager.maps.values()):
                is_selected = index == self.selected_map_index
                if is_selected:
                    highlight = pygame.Rect(108, y - 4, 800, 34)
                    pygame.draw.rect(
                        self.screen, (42, 52, 57), highlight, border_radius=6
                    )
                    pygame.draw.rect(
                        self.screen, self.ACCENT, highlight, width=1, border_radius=6
                    )

                prefix = ">" if is_selected else " "
                self.text(
                    self.body_font,
                    f"{prefix} {map_def.name}  ({map_def.width} x {map_def.height})",
                    120,
                    y,
                    self.ACCENT if is_selected else self.TEXT,
                )
                y += 34
        else:
            self.text(self.body_font, "(ninguno)", 120, y, self.MUTED)

        y += 24
        self.text(self.heading_font, "Criaturas", 110, y, self.TEXT)
        y += 48
        if self.manager.creatures:
            for index, name in enumerate(self.manager.creatures):
                is_selected = index == self.selected_species_index
                if is_selected:
                    highlight = pygame.Rect(108, y - 4, 800, 30)
                    pygame.draw.rect(
                        self.screen, (42, 52, 57), highlight, border_radius=6
                    )
                    pygame.draw.rect(
                        self.screen, self.ACCENT, highlight, width=1, border_radius=6
                    )

                prefix = ">" if is_selected else " "
                self.text(
                    self.body_font,
                    f"{prefix} {name}",
                    120,
                    y,
                    self.ACCENT if is_selected else self.TEXT,
                )
                y += 30
        else:
            self.text(self.body_font, "(ninguna)", 120, y, self.MUTED)

        self.draw_log(y + 26)

        if self.phase == "preparation":
            button_label = "Empezar"
        elif self.paused:
            button_label = "Seguir"
        else:
            button_label = "Pausa"

        pygame.draw.rect(self.screen, self.ACCENT, self.START_BUTTON, border_radius=8)
        label = self.body_font.render(button_label, True, self.BACKGROUND)
        self.screen.blit(label, label.get_rect(center=self.START_BUTTON.center))

        if self.phase == "playing":
            self.text(
                self.heading_font,
                f"Tick {self.world.tick if self.world else 0}  ·  "
                f"{self.ticks_per_second} tps",
                350,
                782,
                self.ACCENT,
            )
            self.text(
                self.small_font,
                "Espacio: un tick  |  P: pausa/seguir",
                350,
                820,
                self.MUTED,
            )
            self.text(self.small_font, "Velocidad", 610, 760, self.MUTED)
            for index, rect in enumerate(self.SPEED_BUTTONS):
                active = index == self.speed_index
                pygame.draw.rect(
                    self.screen,
                    self.ACCENT if active else (42, 52, 57),
                    rect,
                    border_radius=6,
                )
                pygame.draw.rect(
                    self.screen,
                    self.ACCENT,
                    rect,
                    width=1,
                    border_radius=6,
                )
                label = self.body_font.render(
                    str(self.SPEEDS[index]),
                    True,
                    self.BACKGROUND if active else self.TEXT,
                )
                self.screen.blit(label, label.get_rect(center=rect.center))
            self.text(self.small_font, "tps", 842, 796, self.MUTED)

        panel = pygame.Rect(980, 210, 860, 640)
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.ACCENT, panel, width=2, border_radius=10)

        self.text(self.heading_font, "Mapa", 1010, 235, self.TEXT)
        world_map = self.world_map
        if selected is not None and world_map is not None:
            self.text(
                self.small_font,
                f"{selected.name}  ({selected.width} x {selected.height})",
                1010,
                270,
                self.ACCENT,
            )
            self.map_view.draw(
                self.screen,
                world_map,
                self.MAP_RECT,
                selected=self.selected_creature,
            )
        else:
            self.text(self.body_font, "No hay mapas cargados.", 1020, 300, self.MUTED)

        if self.phase == "playing":
            self.draw_inspector()
        else:
            self.draw_errors()

        if self.status:
            self.text(
                self.small_font,
                self.status[:120],
                80,
                975,
                self.ERROR if self.status_is_error else self.ACCENT,
            )

        self.text(
            self.small_font,
            (
                "ESC salir  |  UP/DOWN mapa  |  LEFT/RIGHT especie  |  "
                "click coloca  |  click derecho quita"
                if self.phase == "preparation"
                else "ESC salir  |  click: inspeccionar  |  1/2/3: velocidad  |  "
                "Espacio: un tick  |  P: pausa/seguir  |  R: reiniciar"
            ),
            80,
            1020,
            self.MUTED,
        )

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.draw()
