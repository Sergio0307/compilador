import pygame

from ui.app import InstinctApp


def main():
    pygame.init()

    try:
        app = InstinctApp()
        app.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
