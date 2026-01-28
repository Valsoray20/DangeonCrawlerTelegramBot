from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.filters import Command
import logging
import random

from game.core import DragonGame
from game.items import ItemSystem, ItemType
from render.room_renderer import RoomRenderer
from bot.keyboards import (
    get_move_keyboard, get_combat_keyboard,
    get_inventory_keyboard, get_main_menu_keyboard,
    get_settings_keyboard, get_shop_keyboard
)
from storage.csv_storage import CSVStorage

user_games = {}
user_settings = {}
renderers = {}
storage = CSVStorage()

router = Router()


class UserSettings:
    def __init__(self):
        self.show_hints = True
        self.image_size = "medium"  # small, medium, large
        self.waiting_for = None
        self.temp_data = {}


# Инициализируем рендереры разных размеров
renderers = {
    "small": RoomRenderer(cell_size=20),
    "medium": RoomRenderer(cell_size=40),
    "large": RoomRenderer(cell_size=60)
}


# УПРОЩЁННЫЕ ФУНКЦИИ - БЕЗ СОХРАНЕНИЯ ID СООБЩЕНИЙ
async def send_game_message(bot, chat_id, text: str, reply_markup=None):
    """Просто отправляет сообщение"""
    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )


async def send_game_photo(bot, chat_id, photo_bytes: bytes, caption: str, reply_markup=None):
    """Просто отправляет фото"""
    photo = BufferedInputFile(photo_bytes, filename="room.png")
    return await bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup
    )


# ===== ГЛАВНОЕ МЕНЮ =====

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    storage.save_player(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )

    await send_game_message(
        message.bot, chat_id,
        "🗡️ *Эй, славный герой, готов покорить подземелье?*\n\n"
        "Впереди тебя ждут опасные коридоры, хитрые ловушки "
        "и свирепые монстры! А в самом конце... логово ДРАКОНА! 🐉\n\n"
        "Сможешь ли ты дойти до конца и стать легендой?",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "▶️ Начать игру")
async def start_game(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_settings:
        user_settings[user_id] = UserSettings()

    user_games[user_id] = DragonGame()
    game = user_games[user_id]
    settings = user_settings[user_id]

    await send_game_message(
        message.bot, chat_id,
        "🏃 *Погружение в подземелье...*\n\n"
        "Ты стоишь в стартовой комнате. Вокруг тишина, "
        "но ты чувствуешь - опасность рядом.\n\n"
        "Вперед, искатель приключений!",
        get_move_keyboard(show_hints=settings.show_hints)
    )

    await _send_room_info(message.bot, chat_id, game, user_id)


@router.message(F.text == "⚙️ Настройки")
async def open_settings(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_settings:
        user_settings[user_id] = UserSettings()

    settings = user_settings[user_id]

    size_text = {
        "small": "Маленькие (быстрая загрузка)",
        "medium": "Средние (баланс)",
        "large": "Большие (детализация)"
    }[settings.image_size]

    await send_game_message(
        message.bot, chat_id,
        "⚙️ *Настройки*\n\n"
        f"🔔 *Подсказки*: {'включены' if settings.show_hints else 'выключены'}\n"
        f"🖼️ *Размер изображений*: {size_text}",
        get_settings_keyboard(
            settings.show_hints,
            settings.image_size
        )
    )


@router.message(F.text == "🛠️ Пещера разработчика")
async def show_developer_cave(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await send_game_message(
        message.bot, chat_id,
        "🛠️ *Пещера разработчика*\n\n"
        "Присоединяйся к нашему сообществу!\n\n"
        "Здесь ты найдешь:\n"
        "• Новости об обновлениях\n"
        "• Помощь и советы\n"
        "• Общение с другими игроками\n"
        "• Конкурсы и события\n\n"
        "💎 *Ссылка*: https://t.me/DragonDungeonChanal\n\n"
        "Возвращайся в игру, герой!",
        get_main_menu_keyboard()
    )


@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in user_games:
        del user_games[user_id]

    await send_game_message(
        message.bot, chat_id,
        "Главное меню:",
        get_main_menu_keyboard()
    )


# ===== НАСТРОЙКИ =====

@router.message(F.text.in_(["🔕 Подсказки", "🔔 Подсказки"]))
async def toggle_hints(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_settings:
        user_settings[user_id] = UserSettings()

    settings = user_settings[user_id]
    settings.show_hints = not settings.show_hints

    size_text = {
        "small": "Маленькие (быстрая загрузка)",
        "medium": "Средние (баланс)",
        "large": "Большие (детализация)"
    }[settings.image_size]

    await send_game_message(
        message.bot, chat_id,
        "⚙️ *Настройки*\n\n"
        f"🔔 *Подсказки*: {'включены' if settings.show_hints else 'выключены'}\n"
        f"🖼️ *Размер изображений*: {size_text}",
        get_settings_keyboard(
            settings.show_hints,
            settings.image_size
        )
    )


@router.message(F.text.in_(["🖼️ Маленькие", "🖼️ Средние", "🖼️ Большие"]))
async def change_image_size(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_settings:
        user_settings[user_id] = UserSettings()

    settings = user_settings[user_id]

    if message.text == "🖼️ Маленькие":
        settings.image_size = "small"
    elif message.text == "🖼️ Средние":
        settings.image_size = "medium"
    elif message.text == "🖼️ Большие":
        settings.image_size = "large"

    size_text = {
        "small": "Маленькие (быстрая загрузка)",
        "medium": "Средние (баланс)",
        "large": "Большие (детализация)"
    }[settings.image_size]

    await send_game_message(
        message.bot, chat_id,
        "⚙️ *Настройки*\n\n"
        f"🔔 *Подсказки*: {'включены' if settings.show_hints else 'выключены'}\n"
        f"🖼️ *Размер изображений*: {size_text}",
        get_settings_keyboard(
            settings.show_hints,
            settings.image_size
        )
    )


# ===== ОСНОВНАЯ ИГРА =====

@router.message(F.text.in_(["⬆️", "⬇️", "⬅️", "➡️"]))
async def handle_movement(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    direction_map = {
        "⬆️": (0, -1),
        "⬇️": (0, 1),
        "⬅️": (-1, 0),
        "➡️": (1, 0)
    }

    dx, dy = direction_map[message.text]
    moved, new_room, events = game.move_player(dx, dy)

    if not moved:
        await send_game_message(
            message.bot, chat_id,
            "❌ Туда нельзя!",
            get_move_keyboard(
                show_hints=settings.show_hints,
                in_combat=game.in_combat
            )
        )
        return

    storage.save_game_session(user_id, game.export_session_data())
    for room_data in game.export_all_rooms_data():
        storage.save_room(user_id, room_data)

    if events:
        for event in events:
            await send_game_message(
                message.bot, chat_id,
                event,
                get_move_keyboard(
                    show_hints=settings.show_hints,
                    in_combat=game.in_combat
                )
            )

    if new_room and new_room.is_dragon_room:
        await send_game_message(
            message.bot, chat_id,
            "🔥 *Новая комната: ЛОГОВО ДРАКОНА!* 🔥",
            get_move_keyboard(
                show_hints=settings.show_hints,
                in_combat=game.in_combat
            )
        )

    await _send_room_info(message.bot, chat_id, game, user_id)


@router.message(F.text == "🎒")
async def show_inventory(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    inventory = game.player.inventory

    if not inventory:
        inventory_text = "🎒 *Инвентарь пуст*"
    else:
        inventory_text = "🎒 *Твой инвентарь:*\n\n"
        for item in inventory:
            inventory_text += f"• {item.name}\n"

    if game.player.weapon:
        inventory_text += f"\n⚔️ *Оружие:* {game.player.weapon.name}"
    if game.player.armor:
        inventory_text += f"\n🛡️ *Броня:* {game.player.armor.name}"

    inventory_text += f"\n💰 *Золото:* {game.player.gold}"
    inventory_text += f"\n❤️ *Здоровье:* {game.player.hp}/{game.player.max_hp}"

    await send_game_message(
        message.bot, chat_id,
        inventory_text,
        get_inventory_keyboard(
            show_hints=settings.show_hints
        )
    )


@router.message(F.text == "📦")
async def open_chest(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    success, result = game.open_chest()

    if success:
        storage.save_game_session(user_id, game.export_session_data())
        for room_data in game.export_all_rooms_data():
            storage.save_room(user_id, room_data)

        # Показываем результат открытия сундука
        await send_game_message(
            message.bot, chat_id,
            result,
            get_move_keyboard(
                show_hints=settings.show_hints,
                in_combat=game.in_combat
            )
        )

        # Затем показываем обновленную комнату
        await _send_room_info(message.bot, chat_id, game, user_id)
    else:
        await send_game_message(
            message.bot, chat_id,
            result,
            get_move_keyboard(
                show_hints=settings.show_hints,
                in_combat=game.in_combat
            )
        )


# ===== БОЕВЫЕ ОБРАБОТЧИКИ =====
# ОБРАБОТЧИК АТАКИ В БОЮ
@router.message(F.text == "⚔️ Атаковать")
async def attack_in_combat(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    # Если не в бою, начинаем бой
    if not game.in_combat:
        if game.current_room and game.current_room.monster and game.current_room.monster.hp > 0:
            game.in_combat = True
            game.current_monster = game.current_room.monster

            storage.save_game_session(user_id, game.export_session_data())

            await send_game_message(
                message.bot, chat_id,
                f"⚔️ *БОЙ НАЧАЛСЯ!* ⚔️\n\n"
                f"Противник: {game.current_monster.name}\n"
                f"❤️ Твоё здоровье: {game.player.hp}/{game.player.max_hp}\n"
                f"❤️ Здоровье монстра: {game.current_monster.hp}/{game.current_monster.max_hp}\n\n"
                f"Твоя атака: {game.player.attack_power}\n"
                f"Твоя защита: {game.player.defense}\n\n"
                f"*Нажми:*\n"
                f"• ⚔️ Атаковать - атаковать\n"
                f"• 🏃 Бежать - попытаться убежать\n"
                f"• 💊 - использовать зелье (если есть)\n"
                f"• 🔙 Назад - вернуться в игру",
                get_combat_keyboard(show_hints=settings.show_hints)
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Здесь не с кем сражаться!",
                get_move_keyboard(show_hints=settings.show_hints)
            )
        return

    # Если уже в бою, выполняем атаку
    success, result = game.attack_monster()

    if success:
        storage.save_game_session(user_id, game.export_session_data())
        for room_data in game.export_all_rooms_data():
            storage.save_room(user_id, room_data)

    # Проверяем смерть игрока
    if game.player.hp <= 0:
        await send_game_message(
            message.bot, chat_id,
            f"{result}\n\n💀 *Ты погиб! Игра окончена.*",
            get_main_menu_keyboard()
        )

        storage.update_player_stats(
            user_id=user_id,
            steps=game.player.steps,
            rooms_visited=game.player.rooms_visited,
            dragon_found=game.dragon_found
        )
        storage.end_game_session(user_id)

        if user_id in user_games:
            del user_games[user_id]
        return

    # Показываем результат боя
    await send_game_message(
        message.bot, chat_id,
        result,
        get_combat_keyboard(
            show_hints=settings.show_hints
        ) if game.in_combat else get_move_keyboard(
            show_hints=settings.show_hints
        )
    )

    # Если бой окончен, показываем комнату
    if not game.in_combat and game.player.hp > 0:
        await _send_room_info(message.bot, chat_id, game, user_id)


@router.message(F.text == "🛒")
async def visit_shop(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    success, result = game.visit_shop()

    if success:
        await send_game_message(
            message.bot, chat_id,
            result,
            get_shop_keyboard()
        )
    else:
        settings = user_settings.get(user_id, UserSettings())
        await send_game_message(
            message.bot, chat_id,
            result,
            get_move_keyboard(
                show_hints=settings.show_hints,
                in_combat=game.in_combat
            )
        )


@router.message(F.text == "🔙 Назад")
async def back_to_game(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    # Показываем правильную клавиатуру в зависимости от состояния
    if game.in_combat:
        await send_game_message(
            message.bot, chat_id,
            f"⚔️ *Бой продолжается!*\n\n"
            f"Противник: {game.current_monster.name}\n"
            f"❤️ Твоё здоровье: {game.player.hp}/{game.player.max_hp}\n"
            f"❤️ Здоровье монстра: {game.current_monster.hp}/{game.current_monster.max_hp}",
            get_combat_keyboard(show_hints=settings.show_hints)
        )
    else:
        await _send_room_info(message.bot, chat_id, game, user_id)


# ===== ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ =====

@router.message(F.text == "🏃 Бежать")
async def run_from_combat(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    if game.in_combat:
        if random.random() < 0.7:  # 70% шанс убежать
            game.in_combat = False

            storage.save_game_session(user_id, game.export_session_data())

            await send_game_message(
                message.bot, chat_id,
                "🏃 *Ты успешно убежал от монстра!*",
                get_move_keyboard(show_hints=settings.show_hints, in_combat=False)
            )
            await _send_room_info(message.bot, chat_id, game, user_id)
        else:
            monster_damage = game.current_monster.attack() if game.current_monster else 10
            actual_damage = game.player.take_damage(monster_damage)

            storage.save_game_session(user_id, game.export_session_data())

            await send_game_message(
                message.bot, chat_id,
                f"🏃 *Не удалось убежать!*\n"
                f"🛡️ Монстр атакует: -{actual_damage} HP\n"
                f"❤️ Здоровье: {game.player.hp}/{game.player.max_hp}",
                get_combat_keyboard(show_hints=settings.show_hints)
            )
    else:
        await send_game_message(
            message.bot, chat_id,
            "Сейчас не время для бегства!",
            get_move_keyboard(show_hints=settings.show_hints, in_combat=game.in_combat)
        )


@router.message(F.text == "💊")
async def use_potion(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    potion = None
    for item in game.player.inventory:
        if item.item_type == ItemType.POTION:
            potion = item
            break

    if not potion:
        if game.in_combat:
            await send_game_message(
                message.bot, chat_id,
                "У тебя нет зелий!",
                get_combat_keyboard(show_hints=settings.show_hints)
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "У тебя нет зелий!",
                get_inventory_keyboard(show_hints=settings.show_hints)
            )
        return

    success, result = game.player.use_item(potion.item_id)

    if success:
        storage.save_game_session(user_id, game.export_session_data())

    if game.in_combat:
        await send_game_message(
            message.bot, chat_id,
            result,
            get_combat_keyboard(show_hints=settings.show_hints)
        )
    else:
        await send_game_message(
            message.bot, chat_id,
            result,
            get_inventory_keyboard(show_hints=settings.show_hints)
        )


# ОБРАБОТЧИК ЭКИПИРОВКИ ОРУЖИЯ В ИНВЕНТАРЕ
@router.message(F.text == "🗡️ Оружие")
async def equip_weapon(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    weapons = game.player.get_weapons_from_inventory()

    if not weapons:
        await send_game_message(
            message.bot, chat_id,
            "У тебя нет оружия в инвентаре!",
            get_inventory_keyboard(show_hints=settings.show_hints)
        )
        return

    if len(weapons) == 1:
        success, result = game.player.equip_weapon(weapons[0])
        await send_game_message(
            message.bot, chat_id,
            result,
            get_inventory_keyboard(show_hints=settings.show_hints)
        )
    else:
        weapons_text = "🗡️ *Выбери оружие для экипировки:*\n\n"
        for i, weapon in enumerate(weapons, 1):
            weapons_text += f"{i}. {weapon.name} (урон: {weapon.damage})\n"

        weapons_text += "\nОтправь номер оружия:"

        settings.temp_data['weapons'] = weapons
        settings.waiting_for = 'choose_weapon'

        await send_game_message(
            message.bot, chat_id,
            weapons_text,
            ReplyKeyboardRemove()
        )


@router.message(F.text == "🛡️ Броня")
async def equip_armor(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]
    settings = user_settings.get(user_id, UserSettings())

    armor_list = game.player.get_armor_from_inventory()

    if not armor_list:
        await send_game_message(
            message.bot, chat_id,
            "У тебя нет брони в инвентаре!",
            get_inventory_keyboard(show_hints=settings.show_hints)
        )
        return

    if len(armor_list) == 1:
        success, result = game.player.equip_armor(armor_list[0])
        await send_game_message(
            message.bot, chat_id,
            result,
            get_inventory_keyboard(show_hints=settings.show_hints)
        )
    else:
        armor_text = "🛡️ *Выбери броню для экипировки:*\n\n"
        for i, armor in enumerate(armor_list, 1):
            armor_text += f"{i}. {armor.name} (защита: {armor.defense})\n"

        armor_text += "\nОтправь номер брони:"

        settings.temp_data['armor'] = armor_list
        settings.waiting_for = 'choose_armor'

        await send_game_message(
            message.bot, chat_id,
            armor_text,
            ReplyKeyboardRemove()
        )


@router.message(F.text == "🛒 Купить")
async def buy_item(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_games:
        await send_game_message(
            message.bot, chat_id,
            "Сначала начни игру!",
            get_main_menu_keyboard()
        )
        return

    game = user_games[user_id]

    if not game.current_room or not game.current_room.shop:
        await send_game_message(
            message.bot, chat_id,
            "Здесь нет магазина!",
            get_shop_keyboard()
        )
        return

    shop_items = game.get_shop_items()

    if not shop_items:
        await send_game_message(
            message.bot, chat_id,
            "Магазин пуст!",
            get_shop_keyboard()
        )
        return

    shop_text = "🛒 *Магазин гоблина*\n\n"
    shop_text += f"💰 Твое золото: {game.player.gold}\n\n"
    shop_text += "*Доступные товары:*\n"

    for i, item in enumerate(shop_items, 1):
        price = item.value * 2
        shop_text += f"{i}. {item.name} - {price} золота\n"
        if item.description:
            shop_text += f"   {item.description}\n"

    shop_text += "\nОтправь номер товара для покупки:"

    settings = user_settings.get(user_id, UserSettings())
    settings.temp_data['shop_items'] = shop_items
    settings.waiting_for = 'buy_item'

    await send_game_message(
        message.bot, chat_id,
        shop_text,
        ReplyKeyboardRemove()
    )


# ===== ОБРАБОТЧИК ВЫБОРА =====

@router.message(F.text.regexp(r'^\d+$'))
async def handle_number_input(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_settings:
        return

    settings = user_settings[user_id]
    number = int(message.text)

    if settings.waiting_for == 'choose_weapon':
        weapons = settings.temp_data.get('weapons', [])
        if 1 <= number <= len(weapons):
            weapon = weapons[number - 1]
            success, result = user_games[user_id].player.equip_weapon(weapon)

            settings.waiting_for = None
            settings.temp_data = {}

            await send_game_message(
                message.bot, chat_id,
                result,
                get_inventory_keyboard(show_hints=settings.show_hints)
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Неверный номер оружия!",
                get_inventory_keyboard(show_hints=settings.show_hints)
            )

    elif settings.waiting_for == 'choose_armor':
        armor_list = settings.temp_data.get('armor', [])
        if 1 <= number <= len(armor_list):
            armor = armor_list[number - 1]
            success, result = user_games[user_id].player.equip_armor(armor)

            settings.waiting_for = None
            settings.temp_data = {}

            await send_game_message(
                message.bot, chat_id,
                result,
                get_inventory_keyboard(show_hints=settings.show_hints)
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Неверный номер брони!",
                get_inventory_keyboard(show_hints=settings.show_hints)
            )

    elif settings.waiting_for == 'buy_item':
        shop_items = settings.temp_data.get('shop_items', [])
        if 1 <= number <= len(shop_items):
            success, result = user_games[user_id].buy_item(number - 1)

            settings.waiting_for = None
            settings.temp_data = {}

            await send_game_message(
                message.bot, chat_id,
                result,
                get_shop_keyboard()
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Неверный номер товара!",
                get_shop_keyboard()
            )
    else:
        # Если номер отправлен, но мы не ждем выбора, показываем сообщение
        if user_id in user_games:
            game = user_games[user_id]
            settings = user_settings.get(user_id, UserSettings())
            if game.in_combat:
                await send_game_message(
                    message.bot, chat_id,
                    "Используй кнопки для боя!",
                    get_combat_keyboard(show_hints=settings.show_hints)
                )
            else:
                await send_game_message(
                    message.bot, chat_id,
                    "Используй кнопки для навигации!",
                    get_move_keyboard(show_hints=settings.show_hints)
                )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Используй кнопки для навигации!",
                get_main_menu_keyboard()
            )


async def _send_room_info(bot, chat_id, game: DragonGame, user_id: int):
    settings = user_settings.get(user_id, UserSettings())

    matrix = game.get_current_room_matrix()
    renderer = renderers.get(settings.image_size, renderers["medium"])
    image_bytes = renderer.generate_room_image(matrix)

    room_info = game.get_room_info()

    if settings.show_hints:
        hints = "\n\n💡 *Обозначения:*\n"
        hints += "• ⬜ - Пустота\n"
        hints += "• ⚫ - Стены\n"
        hints += "• ⬛ - Пол\n"
        hints += "• 🟫 - Двери\n"
        hints += "• 🔵 - Ты\n"
        hints += "• 🟥 - Монстры\n"
        hints += "• 🟨 - Сундуки\n"
        hints += "• 🟩 - Магазины"
        room_info += hints

    if game.dragon_found:
        victory_text = "\n\n🎉 *ПОБЕДА! ТЫ НАШЕЛ ЛОГОВО ДРАКОНА!* 🐉\n\n"
        victory_text += "Ты стал легендой! Хочешь еще приключений?"

        await send_game_photo(
            bot, chat_id,
            image_bytes,
            f"{room_info}{victory_text}",
            get_main_menu_keyboard()
        )

        storage.update_player_stats(
            user_id=user_id,
            steps=game.player.steps,
            rooms_visited=game.player.rooms_visited,
            dragon_found=True
        )
        storage.end_game_session(user_id)

        if user_id in user_games:
            del user_games[user_id]
    else:
        # НЕ ПОКАЗЫВАЕМ КАРТУ ВО ВРЕМЯ БОЯ
        if not game.in_combat:
            await send_game_photo(
                bot, chat_id,
                image_bytes,
                room_info,
                get_move_keyboard(
                    show_hints=settings.show_hints
                )
            )
        else:
            # Если в бою, показываем только текстовое сообщение с информацией о бое
            await send_game_message(
                bot, chat_id,
                f"⚔️ *Бой продолжается!*\n\n"
                f"Противник: {game.current_monster.name}\n"
                f"❤️ Твоё здоровье: {game.player.hp}/{game.player.max_hp}\n"
                f"❤️ Здоровье монстра: {game.current_monster.hp}/{game.current_monster.max_hp}",
                get_combat_keyboard(show_hints=settings.show_hints)
            )


@router.message()
async def handle_other_messages(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Логируем что пришло
    print(f"Получено сообщение: {message.text}")

    # Если пользователь в игре, показываем соответствующее сообщение
    if user_id in user_games:
        game = user_games[user_id]
        settings = user_settings.get(user_id, UserSettings())

        # Если есть ожидание ввода, сбрасываем его
        if user_id in user_settings and user_settings[user_id].waiting_for:
            user_settings[user_id].waiting_for = None
            user_settings[user_id].temp_data = {}

        if game.in_combat:
            await send_game_message(
                message.bot, chat_id,
                "Используй кнопки для боя!",
                get_combat_keyboard(show_hints=settings.show_hints)
            )
        else:
            await send_game_message(
                message.bot, chat_id,
                "Используй кнопки для навигации!",
                get_move_keyboard(show_hints=settings.show_hints)
            )
    else:
        # Если не в игре, показываем главное меню
        await send_game_message(
            message.bot, chat_id,
            "Используй кнопки для навигации!",
            get_main_menu_keyboard()
        )