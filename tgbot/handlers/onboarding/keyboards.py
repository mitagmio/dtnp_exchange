from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON
from tgbot.handlers.onboarding.static_text import github_button_text, secret_level_button_text, start_button_text


def make_keyboard_for_start_command() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(github_button_text, url="https://github.com/ohld/django-telegram-bot"),
        InlineKeyboardButton(secret_level_button_text, callback_data=f'{SECRET_LEVEL_BUTTON}')
    ]]

    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_start() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text='✅ Продолжить', callback_data='Меню'),
        ],
    ]

    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_check_username() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(text='✅ Продолжить', callback_data='Меню')
    ]]
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_check_in() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(text='💻 Перейти в канал', url='https://t.me/+NouGXCd7ux4xY2Y6')
    ],[
        InlineKeyboardButton(text='✅ Продолжить', callback_data='Меню')
    ]]
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_menu(adm) -> InlineKeyboardMarkup:
        buttons = []
                # [
        #     InlineKeyboardButton(text='👫🕺 Реферальные ссылки', url='https://t.me/serg_p2p')
        # ],
        # [
        #     InlineKeyboardButton(text='🆘 Помощь', url='https://t.me/serg_p2p'),
        #     InlineKeyboardButton(text='💰💰 Кошелек', callback_data='Кошелек')
        # ]
        btn_vc = InlineKeyboardButton(
            text='📱 Личный кабинет', callback_data='Кошелек')
        btn_ref = InlineKeyboardButton(
            text='👫🕺 Реферальная система', callback_data='Рефералка')
        btn_academy = InlineKeyboardButton(
            text='ℹ️ FAQ', callback_data='FAQ')
        btn_history = InlineKeyboardButton(
            text='🗓🧾 Истории действий', callback_data='История')
        buttons.append([btn_vc])
        buttons.append([btn_ref])
        buttons.append([btn_history])
        buttons.append([btn_academy])
        
        if adm:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_wallet(text_email: str) -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url='https://t.me/serg_p2p')
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
        btn_top_up_usdt = InlineKeyboardButton(
            text='📥 Пополнить', callback_data='Пополнить_Кошелек_TRC20')
        buttons.append([btn_top_up_usdt])
        btn_withdrawal_usdt = InlineKeyboardButton(
            text='📤 Вывести', callback_data='Вывести')
        buttons.append([btn_withdrawal_usdt])
        btn_deactivate_usdt = InlineKeyboardButton(
            text='🔀 Деактивировать счет', callback_data='Деактивировать')
        buttons.append([btn_deactivate_usdt])
        if text_email != '':
            btn_change_email = InlineKeyboardButton(
                text='📨 Изменить почту', callback_data='Почта')
            buttons.append([btn_change_email])
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_top_up_wallet_usdt() -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url='https://t.me/serg_p2p')
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Кошелек')
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_faq() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    btn_1 = InlineKeyboardButton(
            text='1️⃣ О проекте', callback_data='1️⃣')
    buttons.append([btn_1])
    btn_2 = InlineKeyboardButton(
            text='2️⃣ Как пополнить баланс', callback_data='2️⃣')
    buttons.append([btn_2])
    btn_3 = InlineKeyboardButton(
            text='3️⃣ Когда производятся выплаты', callback_data='3️⃣')
    buttons.append([btn_3])
    btn_4 = InlineKeyboardButton(
            text='4️⃣ Какой % я получу от инвестиций', callback_data='4️⃣')
    buttons.append([btn_4])
    btn_5 = InlineKeyboardButton(
            text='5️⃣ Какие риски', callback_data='5️⃣')
    buttons.append([btn_5])
    btn_6 = InlineKeyboardButton(
            text='6️⃣ Смогу ли я вывести все инвестиции', callback_data='6️⃣')
    buttons.append([btn_6])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_help() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_admin() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(
        text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)