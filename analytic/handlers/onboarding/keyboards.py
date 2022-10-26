from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def make_keyboard_for_start(url = '') -> InlineKeyboardMarkup:
    if url == '':
        buttons = [
            [
                InlineKeyboardButton(text='✅ Продолжить', callback_data='Меню'),
            ],
        ]
    if url != '':
        buttons = [
            [
                InlineKeyboardButton(text='✅ Продолжить', url=url),
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
        InlineKeyboardButton(text='💻 Перейти в канал', url='https://t.me/+KoCswat85gBmNjQ6')
    ],[
        InlineKeyboardButton(text='✅ Продолжить', callback_data='Меню')
    ]]
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_menu(adm) -> InlineKeyboardMarkup:
        buttons = []
        
        btn_help = InlineKeyboardButton(text='🆘 Помощь', callback_data='Help')
       
        buttons.append([btn_help])
        
        if adm:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_help() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_admin(is_admin) -> InlineKeyboardMarkup:
    buttons = []
    btn_add_camp = InlineKeyboardButton(text='❇️ Добавить кампанию', callback_data='Добавить_кампанию')
    btn_my_camp = InlineKeyboardButton(text='🔀 Мои кампании', callback_data='Мои_кампании')
    btn_check_user = InlineKeyboardButton(text='🧾 Заполнить чек по пользователю', callback_data='Чек_пользователя')
    btn_ch_camp = InlineKeyboardButton(text='📝 Изменить сумму рекламной кампании', callback_data='Изменить_сумму')
    btn_stat_camp = InlineKeyboardButton(text='📊 Выгрузить статистику', callback_data='Выгрузить_статистику')
    btn_rem_camp = InlineKeyboardButton(text='❌ Удалить кампанию и всех пользователей', callback_data='Удалить_кампанию')
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(
        text='⏮ В начало', callback_data='Старт')
    if is_admin:
        btn_add_camp_moder = InlineKeyboardButton(text='⛑ Назначить кампанию модератору', callback_data='Назначить_кампанию')
        buttons.append([btn_add_camp_moder])
    buttons.append([btn_add_camp])
    buttons.append([btn_my_camp])
    buttons.append([btn_ch_camp])
    buttons.append([btn_check_user])
    buttons.append([btn_stat_camp])
    buttons.append([btn_rem_camp])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_admin_menu_change() -> InlineKeyboardMarkup:
    buttons = []
    btn_change = InlineKeyboardButton(text='📝 Изменить пост', callback_data='изменить_пост')
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Администрирование')
    btn_main = InlineKeyboardButton(
        text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_change])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_admin_menu() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Администрирование')
    btn_main = InlineKeyboardButton(
        text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)