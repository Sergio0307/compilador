from pathlib import Path

import pygame

from loaders.resource_manager import ResourceManager


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

        for error in self.load_errors:
            print(f"aviso: {error}")

    @property
    def map_names(self):
        return list(self.manager.maps)

    def handle_event(self, event):
        if (
            event.type == pygame.QUIT
            or event.type == pygame.KEYDOWN
            and event.key == pygame.K_ESCAPE
        ):
            self.running = False

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

        panel = pygame.Rect(80, 210, 860, 640)
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.ACCENT, panel, width=2, border_radius=10)

        self.text(self.heading_font, "Mapas", 110, 235, self.TEXT)
        y = 285
        if self.manager.maps:
            for map_def in self.manager.maps.values():
                self.text(
                    self.body_font,
                    f"{map_def.name}  ({map_def.width} x {map_def.height})",
                    120,
                    y,
                )
                y += 34
        else:
            self.text(self.body_font, "(ninguno)", 120, y, self.MUTED)

        y += 24
        self.text(self.heading_font, "Criaturas", 110, y, self.TEXT)
        y += 48
        if self.manager.creatures:
            for name in self.manager.creatures:
                self.text(self.body_font, name, 120, y)
                y += 30
        else:
            self.text(self.body_font, "(ninguna)", 120, y, self.MUTED)

        panel = pygame.Rect(980, 210, 860, 640)
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.ACCENT, panel, width=2, border_radius=10)

        self.text(self.heading_font, "Errores de carga", 1010, 235, self.TEXT)
        y = 285
        if self.load_errors:
            for error in self.load_errors[:14]:
                self.text(self.small_font, str(error)[:110], 1020, y, self.ERROR)
                y += 26
        else:
            self.text(self.body_font, "Sin errores.", 1020, y, self.MUTED)

        self.text(
            self.small_font,
            "ESC para salir  |  siguiente paso: elegir mapa y colocar criaturas",
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
