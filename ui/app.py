import pygame


class InstinctApp:
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 60

    def __init__(self):

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
        )

        pygame.display.set_caption("Instinct | Dota Battlefield")

        self.clock = pygame.time.Clock()
        self.running = True

        self.phase = "preparation"

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

    def update(self, dt):
        pass

    def draw(self):
        self.screen.fill((18, 23, 26))

        pygame.display.flip()

    def run(self):

        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0

            for event in pygame.event.get():

                self.handle_event(event)

            self.update(dt)
            self.draw()
