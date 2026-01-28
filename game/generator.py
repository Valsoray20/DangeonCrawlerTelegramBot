import random
from typing import Tuple, List
from game.core import Room, Door, Direction
from game.items import ItemSystem
from game.monsters import MonsterSystem


class DiceSystem:
    @staticmethod
    def roll() -> Tuple[int, int, int]:
        width = random.randint(2, 6)
        height = random.randint(2, 6)
        doors = random.randint(1, 4)
        return width, height, doors


class DungeonGenerator:
    def __init__(self):
        self.room_counter = 0

    def generate_room(self, from_room: Room, exit_door: Door, new_room_id: str) -> Room:
        width, height, num_doors = DiceSystem.roll()

        new_x, new_y = self._calculate_room_position(from_room, exit_door, width, height)

        # Просто комната без названия
        new_room = Room(width, height, new_x, new_y, new_room_id)
        new_room.dice_roll = (width, height, num_doors)

        self._add_entrance_door(new_room, exit_door.direction)
        self._add_random_doors(new_room, num_doors - 1, exit_door.direction)
        self._add_room_features(new_room)

        self.room_counter += 1
        return new_room

    def _add_room_features(self, room: Room):
        from game.items import ItemSystem
        from game.monsters import MonsterSystem

        monster_chance = 0.4
        chest_chance = 0.3
        trap_chance = 0.2
        shop_chance = 0.15

        if random.random() < monster_chance:
            room.monster = MonsterSystem.get_random_monster(room.level)

        if random.random() < chest_chance:
            items = [ItemSystem.get_random_item(room.level) for _ in range(random.randint(1, 3))]
            locked = random.random() < 0.6
            key_type = random.choice(["bronze", "silver", "golden"])

            room.chest = {
                'items': items,
                'locked': locked,
                'key_type': key_type
            }

        if random.random() < trap_chance:
            trap_damage = random.randint(5, 15) + (room.level * 5)
            room.trap = {
                'damage': trap_damage,
                'discovered': False
            }

        if random.random() < shop_chance:
            shop_items = [ItemSystem.get_random_item(room.level) for _ in range(random.randint(3, 5))]
            room.add_shop(shop_items)

    def _calculate_room_position(self, from_room: Room, exit_door: Door, new_width: int, new_height: int) -> Tuple[int, int]:
        corridor_length = 3

        if exit_door.direction == Direction.NORTH:
            return (from_room.pos_x + exit_door.x - new_width // 2,
                    from_room.pos_y - new_height - corridor_length)
        elif exit_door.direction == Direction.SOUTH:
            return (from_room.pos_x + exit_door.x - new_width // 2,
                    from_room.pos_y + from_room.height + corridor_length)
        elif exit_door.direction == Direction.EAST:
            return (from_room.pos_x + from_room.width + corridor_length,
                    from_room.pos_y + exit_door.y - new_height // 2)
        else:
            return (from_room.pos_x - new_width - corridor_length,
                    from_room.pos_y + exit_door.y - new_height // 2)

    def _add_entrance_door(self, room: Room, entrance_direction: Direction):
        opposite_dir = self._get_opposite_direction(entrance_direction)

        if opposite_dir == Direction.NORTH:
            room.add_door(room.width // 2, 0, opposite_dir)
        elif opposite_dir == Direction.SOUTH:
            room.add_door(room.width // 2, room.height - 1, opposite_dir)
        elif opposite_dir == Direction.EAST:
            room.add_door(room.width - 1, room.height // 2, opposite_dir)
        else:
            room.add_door(0, room.height // 2, opposite_dir)

    def _add_random_doors(self, room: Room, num_doors: int, entrance_direction: Direction):
        back_dir = self._get_opposite_direction(entrance_direction)
        possible_dirs = [d for d in Direction if d != back_dir]
        random.shuffle(possible_dirs)

        for i in range(min(num_doors, len(possible_dirs))):
            direction = possible_dirs[i]

            if direction == Direction.NORTH:
                if room.width >= 3:
                    door_x = random.randint(1, room.width - 2)
                    locked = random.random() < 0.2
                    key_type = random.choice(["bronze", "silver", "golden"]) if locked else ""
                    room.add_door(door_x, 0, direction, locked=locked, key_type=key_type)
            elif direction == Direction.SOUTH:
                if room.width >= 3:
                    door_x = random.randint(1, room.width - 2)
                    locked = random.random() < 0.2
                    key_type = random.choice(["bronze", "silver", "golden"]) if locked else ""
                    room.add_door(door_x, room.height - 1, direction, locked=locked, key_type=key_type)
            elif direction == Direction.EAST:
                if room.height >= 3:
                    door_y = random.randint(1, room.height - 2)
                    locked = random.random() < 0.2
                    key_type = random.choice(["bronze", "silver", "golden"]) if locked else ""
                    room.add_door(room.width - 1, door_y, direction, locked=locked, key_type=key_type)
            else:
                if room.height >= 3:
                    door_y = random.randint(1, room.height - 2)
                    locked = random.random() < 0.2
                    key_type = random.choice(["bronze", "silver", "golden"]) if locked else ""
                    room.add_door(0, door_y, direction, locked=locked, key_type=key_type)

    def _get_opposite_direction(self, direction: Direction) -> Direction:
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return opposites[direction]


def create_starting_room(room_id: str) -> Room:
    from game.items import ItemSystem

    start_room = Room(3, 3, 0, 0, room_id)
    start_room.dice_roll = (3, 3, 4)

    start_room.add_door(1, 0, Direction.NORTH)
    start_room.add_door(1, 2, Direction.SOUTH)
    start_room.add_door(2, 1, Direction.EAST)
    start_room.add_door(0, 1, Direction.WEST)

    start_room.chest = {
        'items': [
            ItemSystem.HEALTH_POTION,
            ItemSystem.BRONZE_KEY
        ],
        'locked': False,
        'key_type': ""
    }

    return start_room