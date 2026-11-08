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
    FALLBACK_CREATURE = (210, 210, 210)
    FACTION_COLORS = {
        "radiant": (92, 178, 240),
        "dire": (224, 92, 84),
        "neutral": (226, 188, 82),
    }
    GRID_LINE = (16, 21, 23)

    def __init__(self):
        self.selected_cell = None
        self.hovered_cell = None

    def _layout(self, world_map, rect):
        if world_map is None or world_map.width < 1 or world_map.height < 1:
            return None

        cell_size = min(
            rect.width // world_map.width,
            rect.height // world_map.height,
        )
        if cell_size < 1:
            return None

        grid_width = cell_size * world_map.width
        grid_height = cell_size * world_map.height
        origin_x = rect.x + (rect.width - grid_width) // 2
        origin_y = rect.y + (rect.height - grid_height) // 2
        return cell_size, origin_x, origin_y

    def draw(self, screen, world_map, rect):
        layout = self._layout(world_map, rect)
        if layout is None:
            return

        cell_size, origin_x, origin_y = layout
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

                if cell.creature is not None:
                    center = cell_rect.center
                    radius = max(5, cell_size // 3)
                    color = self.FACTION_COLORS.get(
                        cell.creature.faction, self.FALLBACK_CREATURE
                    )
                    pygame.draw.circle(screen, (12, 16, 18), center, radius + 2)
                    pygame.draw.circle(screen, color, center, radius)
                    label_font = pygame.font.Font(None, max(12, cell_size // 2))
                    label_text = cell.creature.species[:1].upper() or "?"
                    label = label_font.render(
                        label_text, True, (10, 14, 16)
                    )
                    screen.blit(label, label.get_rect(center=center))

                pygame.draw.rect(screen, self.GRID_LINE, cell_rect, 1)

    def handle_click(self, position, world_map, rect):
        return self.screen_to_cell(position, world_map, rect)

    def screen_to_cell(self, position, world_map, rect):
        layout = self._layout(world_map, rect)
        if layout is None:
            return None

        cell_size, origin_x, origin_y = layout
        x = (position[0] - origin_x) // cell_size
        y = (position[1] - origin_y) // cell_size
        if 0 <= x < world_map.width and 0 <= y < world_map.height:
            return x, y
        return None
