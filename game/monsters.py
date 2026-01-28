from typing import Dict, Any
import random


class Monster:
    def __init__(self, monster_id: str, name: str, hp: int, damage: int, gold_reward: int, xp_reward: int):
        self.monster_id = monster_id
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.gold_reward = gold_reward
        self.xp_reward = xp_reward

    def take_damage(self, damage: int) -> bool:
        """Наносит урон монстру, возвращает True если монстр умер"""
        self.hp = max(0, self.hp - damage)
        return self.hp <= 0

    def attack(self) -> int:
        """Атака монстра, возвращает урон"""
        return random.randint(self.damage // 2, self.damage)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'monster_id': self.monster_id,
            'name': self.name,
            'max_hp': self.max_hp,
            'hp': self.hp,
            'damage': self.damage,
            'gold_reward': self.gold_reward,
            'xp_reward': self.xp_reward
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        monster = cls(
            monster_id=data['monster_id'],
            name=data['name'],
            hp=data['max_hp'],
            damage=data['damage'],
            gold_reward=data['gold_reward'],
            xp_reward=data['xp_reward']
        )
        monster.hp = data['hp']
        return monster


class MonsterSystem:
    # Слабые монстры
    BAT = Monster("bat", "🦇 Кровососущая мышь", hp=15, damage=3, gold_reward=5, xp_reward=10)
    RAT = Monster("rat", "🐀 Гигантская крыса", hp=20, damage=4, gold_reward=8, xp_reward=15)
    SPIDER = Monster("spider", "🕷️ Ядовитый паук", hp=25, damage=5, gold_reward=12, xp_reward=20)

    # Средние монстры
    GOBLIN = Monster("goblin", "👺 Гоблин-разбойник", hp=40, damage=8, gold_reward=20, xp_reward=30)
    SKELETON = Monster("skeleton", "💀 Воин-скелет", hp=35, damage=10, gold_reward=25, xp_reward=35)
    ZOMBIE = Monster("zombie", "🧟 Полуразложившийся зомби", hp=50, damage=7, gold_reward=18, xp_reward=25)

    # Сильные монстры
    ORC = Monster("orc", "👹 Орк-берсерк", hp=70, damage=15, gold_reward=40, xp_reward=50)
    TROLL = Monster("troll", "🧌 Пещерный тролль", hp=90, damage=12, gold_reward=35, xp_reward=45)
    MINOTAUR = Monster("minotaur", "🐂 Минотавр", hp=80, damage=18, gold_reward=50, xp_reward=60)

    # Боссы
    DRAGON = Monster("dragon", "🐉 Древний дракон", hp=150, damage=25, gold_reward=100, xp_reward=100)

    @classmethod
    def get_random_monster(cls, room_level: int = 1) -> Monster:
        """Генерирует случайного монстра в зависимости от уровня комнаты"""
        # Клонируем монстра чтобы избежать ссылок
        import copy

        monsters_by_level = {
            1: [cls.BAT, cls.RAT, cls.SPIDER],
            2: [cls.GOBLIN, cls.SKELETON, cls.ZOMBIE],
            3: [cls.ORC, cls.TROLL, cls.MINOTAUR],
            4: [cls.DRAGON]
        }

        # Выбираем уровень монстра на основе уровня комнаты
        available_levels = [level for level in monsters_by_level.keys() if level <= room_level]
        if not available_levels:
            available_levels = [1]

        level = random.choice(available_levels)

        return copy.deepcopy(random.choice(monsters_by_level[level]))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return Monster.from_dict(data)