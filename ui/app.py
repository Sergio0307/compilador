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
        self.status = ""
        self.status_is_error = False
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
        selected = self.selected_map
        if selected is None:
            self.world_map = None
            self.world = None
            return

        self.world_map = selected.build()
        self.world = World(self.world_map)

    def place_creature(self, position):
        if self.world is None:
            self.set_status("No hay un mapa cargado.", error=True)
            return

        species = self.selected_species
        if species is None:
            self.set_status("No hay criaturas cargadas.", error=True)
            return

        cell = self.map_view.screen_to_cell(position, self.world_map, self.MAP_RECT)
        if cell is None:
            return

        try:
            creature = self.world.add_creature(species, cell[0], cell[1])
        except ValueError as exc:
            self.set_status(str(exc), error=True)
        else:
            self.set_status(f"{creature.species} colocado en ({cell[0]}, {cell[1]})")

    def set_status(self, message, error=False):
        self.status = message
        self.status_is_error = error

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in (pygame.K_UP, pygame.K_DOWN) and self.manager.maps:
                step = -1 if event.key == pygame.K_UP else 1
                self.selected_map_index = (self.selected_map_index + step) % len(
                    self.manager.maps
                )
                self.rebuild_map()
                self.set_status("")
            elif (
                event.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.manager.creatures
            ):
                step = -1 if event.key == pygame.K_LEFT else 1
                self.selected_species_index = (
                    self.selected_species_index + step
                ) % len(self.manager.creatures)
                self.set_status("")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.place_creature(event.pos)

    def update(self, dt):
        pass

    def text(self, font, text, x, y, color=None):
        surface = font.render(text, True, color or self.TEXT)
        self.screen.blit(surface, (x, y))

    def draw(self):
        self.screen.fill(self.BACKGROUND)

        self.text(self.title_font, "INSTINCT", 80, 60, self.ACCENT)
        self.text(
            self.body_font,
            "Preparación — contenido cargado desde terrains/, objects/, maps/ y creatures/",
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

        panel = pygame.Rect(980, 210, 860, 640)
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.ACCENT, panel, width=2, border_radius=10)

        self.text(self.heading_font, "Mapa", 1010, 235, self.TEXT)
        if selected is not None:
            self.text(
                self.small_font,
                f"{selected.name}  ({selected.width} x {selected.height})",
                1010,
                270,
                self.ACCENT,
            )
            self.map_view.draw(
                self.screen,
                self.world_map,
                self.MAP_RECT,
            )
        else:
            self.text(self.body_font, "No hay mapas cargados.", 1020, 300, self.MUTED)

        self.text(self.heading_font, "Errores de carga", 1010, 680, self.TEXT)
        y = 720
        if self.load_errors:
            for error in self.load_errors[:4]:
                self.text(self.small_font, str(error)[:110], 1020, y, self.ERROR)
                y += 24
        else:
            self.text(self.body_font, "Sin errores.", 1020, y, self.MUTED)

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
            "ESC salir  |  UP/DOWN mapa  |  LEFT/RIGHT especie  |  click coloca criatura",
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
