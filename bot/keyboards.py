from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [KeyboardButton(text="▶️ Начать игру")],
        [KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🛠️ Пещера разработчика")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_settings_keyboard(
        show_hints: bool = True,
        image_size: str = "medium"
) -> ReplyKeyboardMarkup:
    """Клавиатура настроек"""
    hint_button = "🔕 Подсказки" if show_hints else "🔔 Подсказки"

    # Кнопка размера изображения
    size_button = {
        "small": "🖼️ Маленькие",
        "medium": "🖼️ Средние",
        "large": "🖼️ Большие"
    }[image_size]

    buttons = [
        [KeyboardButton(text=hint_button), KeyboardButton(text=size_button)],
        [KeyboardButton(text="🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_move_keyboard(
        show_hints: bool = True,
        in_combat: bool = False
) -> ReplyKeyboardMarkup:
    """Основная клавиатура для игры"""
    if in_combat:
        return get_combat_keyboard(show_hints)

    hint_button = "🔕 Подсказки" if show_hints else "🔔 Подсказки"

    buttons = [
        [KeyboardButton(text="⬆️"), KeyboardButton(text="⬇️")],
        [KeyboardButton(text="⬅️"), KeyboardButton(text="➡️")],
        [KeyboardButton(text="🎒"), KeyboardButton(text="📦")],
        [KeyboardButton(text="⚔️"), KeyboardButton(text="🛒")],
        [KeyboardButton(text="🔙"), KeyboardButton(text=hint_button)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# В функции get_combat_keyboard:
def get_combat_keyboard(show_hints=True):
    buttons = [
        [KeyboardButton(text="⚔️ Атаковать"), KeyboardButton(text="🏃 Бежать")],
        [KeyboardButton(text="💊")]
    ]

    if show_hints:
        buttons.append([KeyboardButton(text="💡 Подсказки")])

    buttons.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# В функции get_inventory_keyboard:
def get_inventory_keyboard(show_hints=True):
    buttons = [
        [KeyboardButton(text="🗡️ Оружие"), KeyboardButton(text="🛡️ Броня")],
        [KeyboardButton(text="💊")]
    ]

    if show_hints:
        buttons.append([KeyboardButton(text="💡 Подсказки")])

    buttons.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_shop_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура магазина"""
    buttons = [
        [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)