from enum import Enum
from typing import Dict, Any
import random
import copy


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    KEY = "key"
    SCROLL = "scroll"
    TREASURE = "treasure"


class Item:
    def __init__(self, item_id: str, name: str, item_type: ItemType, value: int = 0, description: str = ""):
        self.item_id = item_id
        self.name = name
        self.item_type = item_type
        self.value = value
        self.description = description

    def use(self, player):
        if self.item_type == ItemType.POTION:
            old_hp = player.hp
            healed = player.heal(self.value)
            return f"Вы использовали {self.name} и восстановили {healed} HP!"
        elif self.item_type == ItemType.TREASURE:
            player.gold += self.value
            return f"Вы продали {self.name} за {self.value} золота!"
        return f"Вы использовали {self.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'item_id': self.item_id,
            'name': self.name,
            'type': self.item_type.value,
            'value': self.value,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            item_id=data['item_id'],
            name=data['name'],
            item_type=ItemType(data['type']),
            value=data['value'],
            description=data['description']
        )


class Weapon(Item):
    def __init__(self, item_id: str, name: str, damage: int, value: int = 0):
        super().__init__(item_id, name, ItemType.WEAPON, value, f"Оружие с уроном {damage}")
        self.damage = damage

    def to_dict(self):
        data = super().to_dict()
        data['damage'] = self.damage
        return data


class Armor(Item):
    def __init__(self, item_id: str, name: str, defense: int, value: int = 0):
        super().__init__(item_id, name, ItemType.ARMOR, value, f"Броня с защитой {defense}")
        self.defense = defense

    def to_dict(self):
        data = super().to_dict()
        data['defense'] = self.defense
        return data


class ItemSystem:
    # Зелья
    HEALTH_POTION = Item("health_potion", "💊 Зелье здоровья", ItemType.POTION, 30, "Восстанавливает 30 HP")
    MANA_POTION = Item("mana_potion", "🔮 Зелье маны", ItemType.POTION, 0, "Восстанавливает ману")

    # Ключи
    BRONZE_KEY = Item("bronze_key", "🔑 Бронзовый ключ", ItemType.KEY, 10, "Открывает бронзовые замки")
    SILVER_KEY = Item("silver_key", "🔑 Серебряный ключ", ItemType.KEY, 25, "Открывает серебряные замки")
    GOLDEN_KEY = Item("golden_key", "🔑 Золотой ключ", ItemType.KEY, 50, "Открывает золотые замки")

    # Оружие
    IRON_SWORD = Weapon("iron_sword", "⚔️ Железный меч", damage=5, value=15)
    STEEL_SWORD = Weapon("steel_sword", "⚔️ Стальной меч", damage=8, value=30)
    DRAGON_SLAYER = Weapon("dragon_slayer", "⚔️ Убийца драконов", damage=15, value=100)

    # Броня
    LEATHER_ARMOR = Armor("leather_armor", "🛡️ Кожаная броня", defense=2, value=10)
    CHAIN_MAIL = Armor("chain_mail", "🛡️ Кольчуга", defense=4, value=25)
    PLATE_ARMOR = Armor("plate_armor", "🛡️ Латная броня", defense=7, value=50)

    # Сокровища
    GOLD_COINS = Item("gold_coins", "💰 Мешок золотых монет", ItemType.TREASURE, 50, "Можно продать за золото")
    DIAMOND = Item("diamond", "💎 Алмаз", ItemType.TREASURE, 100, "Драгоценный камень")

    @staticmethod
    def get_random_item(room_level: int = 1) -> Item:
        """Генерирует случайный предмет в зависимости от уровня комнаты"""
        # Предметы сгруппированы по уровням
        common_items = [ItemSystem.HEALTH_POTION, ItemSystem.BRONZE_KEY]
        uncommon_items = [ItemSystem.IRON_SWORD, ItemSystem.LEATHER_ARMOR, ItemSystem.SILVER_KEY]
        rare_items = [ItemSystem.STEEL_SWORD, ItemSystem.CHAIN_MAIL, ItemSystem.GOLDEN_KEY, ItemSystem.GOLD_COINS]
        epic_items = [ItemSystem.DRAGON_SLAYER, ItemSystem.PLATE_ARMOR, ItemSystem.DIAMOND]

        # Выбираем группу предметов в зависимости от уровня
        if room_level == 1:
            items = common_items + uncommon_items
        elif room_level == 2:
            items = common_items + uncommon_items + rare_items
        elif room_level == 3:
            items = uncommon_items + rare_items + epic_items
        else:  # room_level >= 4
            items = rare_items + epic_items

        # Клонируем предмет, чтобы избежать ссылок
        item = copy.deepcopy(random.choice(items))

        # Для сокровищ устанавливаем случайное значение золота в зависимости от уровня
        if item.item_type == ItemType.TREASURE:
            item.value = random.randint(room_level * 10, room_level * 30)

        return item

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        item_type = ItemType(data['type'])
        if item_type == ItemType.WEAPON:
            return Weapon(
                item_id=data['item_id'],
                name=data['name'],
                damage=data['damage'],
                value=data['value']
            )
        elif item_type == ItemType.ARMOR:
            return Armor(
                item_id=data['item_id'],
                name=data['name'],
                defense=data['defense'],
                value=data['value']
            )
        else:
            return Item(
                item_id=data['item_id'],
                name=data['name'],
                item_type=item_type,
                value=data['value'],
                description=data['description']
            )