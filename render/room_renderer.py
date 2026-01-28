from PIL import Image, ImageDraw
from typing import List
import io
import random


class RoomRenderer:
    def __init__(self, cell_size: int = 40):
        self.cell_size = cell_size
        self.image_size = 8 * self.cell_size
        self.colors = {
            0: (20, 20, 20),  # Пустота
            1: (60, 60, 60),  # Стены
            2: (140, 140, 140),  # Пол
            3: (160, 120, 80),  # Двери
            4: (30, 144, 255),  # Игрок
            5: (120, 80, 40),  # Запертая дверь
            6: (200, 180, 60),  # Сундук
            7: (255, 0, 0),  # Монстр
            8: (255, 255, 0),  # Ловушка
            9: (0, 255, 0)  # Магазин
        }

    def set_cell_size(self, size: int):
        """Устанавливает размер клетки"""
        self.cell_size = size
        self.image_size = 8 * self.cell_size

    def matrix_to_image(self, matrix: List[List[int]]) -> Image.Image:
        image = Image.new('RGB', (self.image_size, self.image_size), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)

        for y in range(8):
            for x in range(8):
                cell_type = matrix[y][x]
                color = self.colors.get(cell_type, (0, 0, 0))

                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(40, 40, 40))

                # Упрощенная отрисовка - только основные элементы
                if cell_type == 2 and (x + y) % 2 == 0:  # Пол
                    dark_color = tuple(max(0, c - 20) for c in color)
                    draw.rectangle([x1, y1, x2, y2], fill=dark_color)

                elif cell_type == 3:  # Двери (просто коричневый квадрат)
                    pass

                elif cell_type == 5:  # Запертая дверь
                    lock_x = x1 + self.cell_size // 2
                    lock_y = y1 + self.cell_size // 2
                    lock_size = self.cell_size // 8
                    draw.rectangle(
                        [lock_x - lock_size, lock_y - lock_size,
                         lock_x + lock_size, lock_y + lock_size],
                        fill=(200, 200, 200)
                    )

                elif cell_type == 6:  # Сундук (желтый квадрат)
                    draw.rectangle(
                        [x1 + 4, y1 + 4, x2 - 4, y2 - 4],
                        fill=(200, 180, 60), outline=(180, 160, 40)
                    )

                elif cell_type == 7:  # Монстр (красный круг)
                    center_x = x1 + self.cell_size // 2
                    center_y = y1 + self.cell_size // 2
                    radius = self.cell_size // 3
                    draw.ellipse(
                        [center_x - radius, center_y - radius,
                         center_x + radius, center_y + radius],
                        fill=color
                    )

                elif cell_type == 8:  # Ловушка (желтый треугольник)
                    draw.polygon(
                        [
                            (x1 + self.cell_size // 2, y1 + 4),
                            (x1 + 4, y2 - 4),
                            (x2 - 4, y2 - 4)
                        ],
                        fill=(255, 255, 0)
                    )

                elif cell_type == 9:  # Магазин (зеленый квадрат с G)
                    draw.rectangle(
                        [x1 + 3, y1 + 3, x2 - 3, y2 - 3],
                        fill=(0, 200, 0), outline=(0, 150, 0)
                    )
                    if self.cell_size >= 20:
                        draw.text(
                            (x1 + self.cell_size // 3, y1 + self.cell_size // 3),
                            "G", fill=(0, 0, 0)
                        )

                elif cell_type == 4:  # Игрок (синий круг)
                    center_x = x1 + self.cell_size // 2
                    center_y = y1 + self.cell_size // 2
                    radius = self.cell_size // 3
                    draw.ellipse(
                        [center_x - radius, center_y - radius,
                         center_x + radius, center_y + radius],
                        fill=color
                    )

        return image

    def generate_room_image(self, matrix: List[List[int]]) -> bytes:
        image = self.matrix_to_image(matrix)

        bio = io.BytesIO()
        image.save(bio, format='PNG')
        bio.seek(0)
        return bio.getvalue()