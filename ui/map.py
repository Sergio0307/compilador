import typing

import pygame


class MapView:
    """Dibuja un WorldMap como una matriz de celdas."""

    TERRAIN_COLORS = {
        "Grass": (58, 92, 54),
        "River": (40, 92, 120),
        "HighGround": (108, 92, 62),
    }
    OBJECT_COLORS = {
        "Rock": (126, 126, 120),
        "Tree": (48, 86, 48),
        "Rune": (150, 94, 170),
    }
    FALLBACK_TERRAIN = (78, 78, 78)
    FALLBACK_OBJECT = (140, 108, 160)
    GRID_LINE = (16, 21, 23)

    def __init__(self):
        self.selected_cell = None
        self.hovered_cell = None

    def draw(self, screen, world_map, rect):
        if world_map is None or world_map.width < 1 or world_map.height < 1:
            return

        cell_size = min(
            rect.width // world_map.width,
            rect.height // world_map.height,
        )
        if cell_size < 1:
            return

        grid_width = cell_size * world_map.width
        grid_height = cell_size * world_map.height
        origin_x = rect.x + (rect.width - grid_width) // 2
        origin_y = rect.y + (rect.height - grid_height) // 2

        for y, row in enumerate(world_map.grid):
            for x, cell in enumerate(row):
                cell_rect = pygame.Rect(
                    origin_x + x * cell_size,
                    origin_y + y * cell_size,
                    cell_size,
                    cell_size,
                )
                terrain_color = self.TERRAIN_COLORS.get(
                    cell.terrain.name, self.FALLBACK_TERRAIN
                )
                pygame.draw.rect(screen, terrain_color, cell_rect)

                if cell.obj is not None:
                    inset = max(2, cell_size // 5)
                    object_rect = cell_rect.inflate(-2 * inset, -2 * inset)
                    object_color = self.OBJECT_COLORS.get(
                        cell.obj.name, self.FALLBACK_OBJECT
                    )
                    pygame.draw.rect(
                        screen,
                        object_color,
                        object_rect,
                        border_radius=max(2, cell_size // 10),
                    )

                pygame.draw.rect(screen, self.GRID_LINE, cell_rect, 1)

    def handle_click(self, position, world):
        pass

    def screen_to_cell(self, position, world, rect):
        pass
