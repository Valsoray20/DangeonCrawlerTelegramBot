from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import random

from game.items import Item, Weapon, Armor, ItemSystem
from game.monsters import Monster, MonsterSystem


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)


@dataclass
class Door:
    x: int
    y: int
    direction: Direction
    connected: bool = False
    target_room_id: Optional[str] = None
    locked: bool = False
    key_type: str = ""


class Room:
    def __init__(self, width: int, height: int, pos_x: int, pos_y: int, room_id: str):
        self.width = width
        self.height = height
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.room_id = room_id
        self.doors: List[Door] = []
        self.explored = False
        self.dice_roll: Optional[Tuple[int, int, int]] = None
        self.monster: Optional[Monster] = None
        self.chest: Optional[Dict[str, Any]] = None
        self.trap: Optional[Dict[str, Any]] = None
        self.shop: Optional[Dict[str, Any]] = None
        self.shop_items: List[Item] = []

    @property
    def is_dragon_room(self) -> bool:
        return self.width == 6 and self.height == 6

    @property
    def level(self) -> int:
        """Уровень комнаты для балансировки монстров и предметов"""
        if self.is_dragon_room:
            return 4
        elif self.width >= 5 or self.height >= 5:
            return 3
        elif self.width <= 2 or self.height <= 2:
            return 1
        else:
            return 2

    def add_door(self, x: int, y: int, direction: Direction, locked: bool = False, key_type: str = ""):
        self.doors.append(Door(x, y, direction, locked=locked, key_type=key_type))

    def get_door_at_local(self, local_x: int, local_y: int) -> Optional[Door]:
        for door in self.doors:
            if door.x == local_x and door.y == local_y:
                return door
        return None

    def get_matrix(self, player_pos: Tuple[int, int]) -> List[List[int]]:
        matrix = [[0 for _ in range(8)] for _ in range(8)]

        start_x = (8 - self.width) // 2
        start_y = (8 - self.height) // 2

        # Заполняем пол
        for y in range(self.height):
            for x in range(self.width):
                if 0 <= start_y + y < 8 and 0 <= start_x + x < 8:
                    matrix[start_y + y][start_x + x] = 2

        # Добавляем стены
        for y in range(start_y - 1, start_y + self.height + 1):
            for x in range(start_x - 1, start_x + self.width + 1):
                if 0 <= x < 8 and 0 <= y < 8:
                    is_door = any(
                        (door.direction == Direction.NORTH and x == start_x + door.x and y == start_y - 1) or
                        (door.direction == Direction.SOUTH and x == start_x + door.x and y == start_y + self.height) or
                        (door.direction == Direction.EAST and x == start_x + self.width and y == start_y + door.y) or
                        (door.direction == Direction.WEST and x == start_x - 1 and y == start_y + door.y)
                        for door in self.doors
                    )
                    if not is_door and (x == start_x - 1 or x == start_x + self.width or
                                        y == start_y - 1 or y == start_y + self.height):
                        matrix[y][x] = 1

        # Добавляем двери
        for door in self.doors:
            if door.direction == Direction.NORTH:
                door_x = start_x + door.x
                door_y = start_y - 1
            elif door.direction == Direction.SOUTH:
                door_x = start_x + door.x
                door_y = start_y + self.height
            elif door.direction == Direction.EAST:
                door_x = start_x + self.width
                door_y = start_y + door.y
            else:  # WEST
                door_x = start_x - 1
                door_y = start_y + door.y

            if 0 <= door_x < 8 and 0 <= door_y < 8:
                matrix[door_y][door_x] = 3 if not door.locked else 5

        # Добавляем сундук
        if self.chest:
            chest_x = start_x + self.width // 2
            chest_y = start_y + self.height // 2
            if 0 <= chest_x < 8 and 0 <= chest_y < 8:
                matrix[chest_y][chest_x] = 6

        # Добавляем монстра
        if self.monster and self.monster.hp > 0:
            monster_x = start_x + (self.width // 3)
            monster_y = start_y + (self.height // 3)
            if 0 <= monster_x < 8 and 0 <= monster_y < 8:
                matrix[monster_y][monster_x] = 7

        # Добавляем ловушку (если не обнаружена)
        if self.trap and not self.trap['discovered']:
            trap_x = start_x + (2 * self.width // 3)
            trap_y = start_y + (2 * self.height // 3)
            if 0 <= trap_x < 8 and 0 <= trap_y < 8:
                matrix[trap_y][trap_x] = 8

        # Добавляем магазин гоблина
        if self.shop:
            shop_x = start_x + (self.width // 4)
            shop_y = start_y + (3 * self.height // 4)
            if 0 <= shop_x < 8 and 0 <= shop_y < 8:
                matrix[shop_y][shop_x] = 9

        # Добавляем игрока
        player_room_x = player_pos[0] - self.pos_x
        player_room_y = player_pos[1] - self.pos_y
        if (0 <= player_room_x < self.width and
                0 <= player_room_y < self.height):
            player_x = start_x + player_room_x
            player_y = start_y + player_room_y
            if 0 <= player_x < 8 and 0 <= player_y < 8:
                matrix[player_y][player_x] = 4

        return matrix

    def add_shop(self, shop_items: List[Item]):
        """Добавляет магазин в комнату"""
        self.shop = {
            'items': shop_items,
            'visited': False
        }
        self.shop_items = shop_items

    def buy_from_shop(self, item_index: int, player) -> Tuple[bool, str]:
        """Покупка предмета из магазина"""
        if not self.shop or item_index < 0 or item_index >= len(self.shop_items):
            return False, "Неверный выбор предмета!"

        item = self.shop_items[item_index]
        price = item.value * 2

        if player.gold >= price:
            player.gold -= price
            if player.add_item(item):
                self.shop_items.pop(item_index)
                return True, f"Вы купили {item.name} за {price} золота!"
            else:
                return False, "Недостаточно места в инвентаре!"
        else:
            return False, f"Недостаточно золота! Нужно {price} золота."


class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.steps = 0
        self.rooms_visited = 1

        # Упрощенные характеристики
        self.max_hp = 100
        self.hp = self.max_hp
        self.gold = 0

        # Экипировка
        self.weapon: Optional[Weapon] = None
        self.armor: Optional[Armor] = None

        # Инвентарь
        self.inventory: List[Item] = []

    @property
    def attack_power(self) -> int:
        base_attack = 10
        if self.weapon:
            base_attack += self.weapon.damage
        return base_attack

    @property
    def defense(self) -> int:
        base_defense = 5
        if self.armor:
            base_defense += self.armor.defense
        return base_defense

    def take_damage(self, damage: int) -> int:
        actual_damage = max(1, damage - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def add_item(self, item: Item) -> bool:
        """Добавляет предмет в инвентарь"""
        if len(self.inventory) < 20:
            self.inventory.append(item)
            return True
        return False

    def remove_item(self, item_id: str) -> Optional[Item]:
        """Удаляет предмет из инвентаря по ID"""
        for i, item in enumerate(self.inventory):
            if item.item_id == item_id:
                return self.inventory.pop(i)
        return None

    def equip_weapon(self, weapon: Weapon) -> Tuple[bool, str]:
        """Экипирует оружие, возвращает статус и сообщение"""
        if weapon not in self.inventory:
            return False, "Это оружие не в вашем инвентаре"

        if self.weapon:
            self.inventory.append(self.weapon)

        self.weapon = weapon
        self.inventory.remove(weapon)
        return True, f"Вы экипировали {weapon.name}!"

    def equip_armor(self, armor: Armor) -> Tuple[bool, str]:
        """Экипирует броню, возвращает статус и сообщение"""
        if armor not in self.inventory:
            return False, "Эта броня не в вашем инвентаре"

        if self.armor:
            self.inventory.append(self.armor)

        self.armor = armor
        self.inventory.remove(armor)
        return True, f"Вы экипировали {armor.name}!"

    def get_weapons_from_inventory(self) -> List[Weapon]:
        """Возвращает список оружия из инвентаря"""
        from game.items import Weapon
        return [item for item in self.inventory if isinstance(item, Weapon)]

    def get_armor_from_inventory(self) -> List[Armor]:
        """Возвращает список брони из инвентаря"""
        from game.items import Armor
        return [item for item in self.inventory if isinstance(item, Armor)]

    def use_item(self, item_id: str) -> Tuple[bool, str]:
        """Использует предмет из инвентаря по ID"""
        item_to_use = None
        for item in self.inventory:
            if item.item_id == item_id:
                item_to_use = item
                break

        if not item_to_use:
            return False, "Предмет не найден в инвентаре"

        self.remove_item(item_id)
        result = item_to_use.use(self)
        return True, result


class DragonGame:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player = Player(1, 1)
        self.current_room_id: Optional[str] = None
        self.dragon_found = False
        self.generator = None
        self.room_counter = 0
        self.in_combat = False
        self.current_monster: Optional[Monster] = None

        from game.generator import DungeonGenerator, create_starting_room
        self.generator = DungeonGenerator()

        # Создаем стартовую комнату
        start_room = create_starting_room(self._generate_room_id())
        self.rooms[start_room.room_id] = start_room
        self.current_room_id = start_room.room_id
        start_room.explored = True

    def _generate_room_id(self) -> str:
        self.room_counter += 1
        return f"room_{self.room_counter}"

    @property
    def current_room(self) -> Optional[Room]:
        return self.rooms.get(self.current_room_id) if self.current_room_id else None

    def move_player(self, dx: int, dy: int) -> Tuple[bool, Optional[Room], List[str]]:
        events = []
        new_x, new_y = self.player.x + dx, self.player.y + dy

        if not self._can_move_to(new_x, new_y):
            return False, None, events

        old_room_id = self.current_room_id
        self.player.x, self.player.y = new_x, new_y
        self.player.steps += 1

        new_room = self._get_room_at(new_x, new_y)
        if new_room and new_room.room_id != self.current_room_id:
            self.current_room_id = new_room.room_id
            if not new_room.explored:
                new_room.explored = True
                self.player.rooms_visited += 1

        if self.current_room and self.current_room.is_dragon_room:
            self.dragon_found = True
            events.append("🐉 Вы чувствуете присутствие ДРАКОНА!")

        generated_room = None
        door_used = self._is_on_door(new_x, new_y)
        if door_used:
            door, room = self._get_door_at(new_x, new_y)
            if door:
                if door.connected and door.target_room_id:
                    target_room = self.rooms.get(door.target_room_id)
                    if target_room:
                        self._move_to_room_through_door(target_room, door.direction)
                elif not door.connected:
                    generated_room = self.generator.generate_room(room, door, self._generate_room_id())
                    if generated_room:
                        self.rooms[generated_room.room_id] = generated_room
                        door.connected = True
                        door.target_room_id = generated_room.room_id

                        entrance_door = self._find_entrance_door(generated_room, door.direction)
                        if entrance_door:
                            entrance_door.connected = True
                            entrance_door.target_room_id = room.room_id

                        self._move_to_room_through_door(generated_room, door.direction)

        if self.current_room and self.current_room.trap and not self.current_room.trap['discovered']:
            trap = self.current_room.trap
            damage = trap['damage']
            actual_damage = self.player.take_damage(damage)
            events.append(f"💥 Ловушка! -{actual_damage} HP")
            trap['discovered'] = True

        if self.current_room and self.current_room.monster and self.current_room.monster.hp > 0:
            self.in_combat = True
            self.current_monster = self.current_room.monster
            events.append(f"⚔️ {self.current_monster.name}!")

        return True, generated_room, events

    def _move_to_room_through_door(self, target_room: Room, entry_direction: Direction):
        entrance_door = None
        for door in target_room.doors:
            if door.direction == self._get_opposite_direction(entry_direction):
                entrance_door = door
                break

        if entrance_door:
            if entry_direction == Direction.NORTH:
                self.player.x = target_room.pos_x + entrance_door.x
                self.player.y = target_room.pos_y + 1
            elif entry_direction == Direction.SOUTH:
                self.player.x = target_room.pos_x + entrance_door.x
                self.player.y = target_room.pos_y + target_room.height - 2
            elif entry_direction == Direction.EAST:
                self.player.x = target_room.pos_x + 1
                self.player.y = target_room.pos_y + entrance_door.y
            else:
                self.player.x = target_room.pos_x + target_room.width - 2
                self.player.y = target_room.pos_y + entrance_door.y
        else:
            self.player.x = target_room.pos_x + target_room.width // 2
            self.player.y = target_room.pos_y + target_room.height // 2

        self.current_room_id = target_room.room_id
        if not target_room.explored:
            target_room.explored = True
            self.player.rooms_visited += 1

    def _find_entrance_door(self, room: Room, direction: Direction) -> Optional[Door]:
        opposite_dir = self._get_opposite_direction(direction)
        for door in room.doors:
            if door.direction == opposite_dir:
                return door
        return None

    def _get_opposite_direction(self, direction: Direction) -> Direction:
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return opposites[direction]

    def _can_move_to(self, x: int, y: int) -> bool:
        room = self._get_room_at(x, y)
        if room:
            return True
        return self._is_on_door(x, y)

    def _get_room_at(self, x: int, y: int) -> Optional[Room]:
        for room in self.rooms.values():
            room_x = x - room.pos_x
            room_y = y - room.pos_y
            if (0 <= room_x < room.width and
                    0 <= room_y < room.height):
                return room
        return None

    def _is_on_door(self, x: int, y: int) -> bool:
        return self._get_door_at(x, y)[0] is not None

    def _get_door_at(self, x: int, y: int) -> Tuple[Optional[Door], Optional[Room]]:
        for room in self.rooms.values():
            for door in room.doors:
                door_world_x = room.pos_x + door.x
                door_world_y = room.pos_y + door.y

                if door.direction == Direction.NORTH:
                    if x == door_world_x and y == room.pos_y - 1:
                        return door, room
                elif door.direction == Direction.SOUTH:
                    if x == door_world_x and y == room.pos_y + room.height:
                        return door, room
                elif door.direction == Direction.EAST:
                    if x == room.pos_x + room.width and y == door_world_y:
                        return door, room
                elif door.direction == Direction.WEST:
                    if x == room.pos_x - 1 and y == door_world_y:
                        return door, room
        return None, None

    def get_current_room_matrix(self) -> List[List[int]]:
        if self.current_room:
            return self.current_room.get_matrix((self.player.x, self.player.y))
        return [[0 for _ in range(8)] for _ in range(8)]

    def attack_monster(self) -> Tuple[bool, str]:
        if not self.in_combat or not self.current_monster:
            return False, "Нет монстра для атаки"

        player_damage = max(1, self.player.attack_power + random.randint(-2, 2))
        monster_died = self.current_monster.take_damage(player_damage)

        result = f"🎯 Атака: {player_damage} урона!\n"

        if monster_died:
            gold_reward = self.current_monster.gold_reward
            self.player.gold += gold_reward

            result += f"💀 Повержен!\n💰 +{gold_reward} золота"
            self.in_combat = False
            self.current_monster = None
            return True, result
        else:
            monster_damage = self.current_monster.attack()
            actual_damage = self.player.take_damage(monster_damage)
            result += f"🛡️ Контратака: -{actual_damage} HP"

            if self.player.hp <= 0:
                result += f"\n💀 Вы погибли!"
                self.in_combat = False

            return True, result

    def open_chest(self) -> Tuple[bool, str]:
        if not self.current_room or not self.current_room.chest:
            return False, "Нет сундука"

        chest = self.current_room.chest

        if chest['locked']:
            key_type = chest['key_type']
            key_item = next((item for item in self.player.inventory
                             if item.item_type.value == "key" and item.item_id.startswith(key_type)), None)

            if not key_item:
                return False, f"Заперт! Нужен {key_type} ключ"

            self.player.remove_item(key_item.item_id)
            chest['locked'] = False

        items = chest['items']
        rewards = []

        for item in items:
            if self.player.add_item(item):
                rewards.append(item.name)

        self.current_room.chest = None

        return True, f"🎁 Получено: {', '.join(rewards)}"

    def get_room_info(self) -> str:
        room = self.current_room
        if not room:
            return ""

        info = f"❤️ {self.player.hp}/{self.player.max_hp} HP\n"
        info += f"💰 {self.player.gold} золота\n"

        if self.player.weapon:
            info += f"⚔️ {self.player.weapon.name}\n"
        if self.player.armor:
            info += f"🛡️ {self.player.armor.name}\n"

        if room.monster and room.monster.hp > 0:
            info += f"⚔️ {room.monster.name} ({room.monster.hp} HP)\n"
        if room.chest:
            status = "🔒" if room.chest['locked'] else "📦"
            info += f"{status} Сундук\n"
        if room.trap and not room.trap['discovered']:
            info += "💥 Ловушка!\n"
        if room.shop:
            info += "🛒 Магазин\n"

        if room.is_dragon_room:
            info += "\n🐉 ЛОГОВО ДРАКОНА!\n"

        return info

    def visit_shop(self) -> Tuple[bool, str]:
        if not self.current_room or not self.current_room.shop:
            return False, "Нет магазина!"

        self.current_room.shop['visited'] = True
        return True, "Добро пожаловать в магазин!"

    def get_shop_items(self) -> List[Item]:
        if self.current_room and self.current_room.shop:
            return self.current_room.shop_items
        return []

    def buy_item(self, item_index: int) -> Tuple[bool, str]:
        if not self.current_room or not self.current_room.shop:
            return False, "Магазин недоступен!"

        return self.current_room.buy_from_shop(item_index, self.player)

    # ДОБАВЛЕННЫЕ МЕТОДЫ ДЛЯ СОХРАНЕНИЯ ДАННЫХ
    def export_session_data(self) -> Dict[str, Any]:
        """Экспортирует данные текущей игровой сессии"""
        return {
            'steps': self.player.steps,
            'rooms_visited': self.player.rooms_visited,
            'dragon_found': self.dragon_found,
            'gold': self.player.gold,
            'hp': self.player.hp,
            'max_hp': self.player.max_hp,
            'in_combat': self.in_combat,
            'current_room_id': self.current_room_id
        }

    def export_all_rooms_data(self) -> List[Dict[str, Any]]:
        """Экспортирует данные всех комнат"""
        rooms_data = []
        for room in self.rooms.values():
            room_data = {
                'room_id': room.room_id,
                'pos_x': room.pos_x,
                'pos_y': room.pos_y,
                'width': room.width,
                'height': room.height,
                'explored': room.explored,
                'has_monster': room.monster is not None and room.monster.hp > 0,
                'has_chest': room.chest is not None,
                'has_trap': room.trap is not None,
                'has_shop': room.shop is not None,
                'metadata': {
                    'dice_roll': room.dice_roll,
                    'doors_count': len(room.doors),
                    'is_dragon_room': room.is_dragon_room,
                    'level': room.level
                }
            }
            rooms_data.append(room_data)
        return rooms_data