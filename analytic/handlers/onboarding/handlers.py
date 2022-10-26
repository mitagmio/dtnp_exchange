import datetime
import time
from json import dumps, loads
from types import SimpleNamespace

from django.db.models import Sum
from django.utils import timezone
from telegram import Bot, ParseMode, Update, Message
from telegram.ext import CallbackContext
from traitlets import Float

from analytic.handlers.onboarding import static_text, static_state
from analytic.handlers.utils.info import extract_user_data_from_update, send_typing_action, is_number
from analytic.handlers.utils.util import _get_csv_from_qs_values
from analytic.models import User, Campaign, History
from analytic.handlers.onboarding.keyboards import *
from tgbot.handlers.broadcast_message.utils import _from_celery_entities_to_entities

# Отслеживаем вход в группу и назначаем рефералом в случае приглашения нового пользователя.


def status_handler_func(update: Update, context: CallbackContext):
    print('status_handler_func', update)
    # if hasattr(update, 'message') and update.message != None:
        # if update.message.chat.id == -1001793015412:
            # User.set_ref_user(update, context)

# Принимаем любой текст и проверяем состояние пользователя


def message_handler_func(update: Update, context: CallbackContext):
    #print('message_handler_func', update)
    if hasattr(update, 'message') and update.message != None:
        u = User.get_user(update, context)
        if update.message.chat.id != -1001793015412:
            if u.state in State_Dict:
                func_menu = State_Dict[u.state]
                func_menu(update, context)
            elif update.message.text in Menu_Dict:  # button_message проверяем текст на соответствие любой кнопке
                func_menu = Menu_Dict[update.message.text]
                func_menu(update, context)
            else:
                del_mes(update, context)


def callback_inline(update: Update, context: CallbackContext):
    # Если сообщение из чата с ботом
    # print('callback_inline', update)
    call_list = [''
                 ]
    call = update.callback_query
    if call.message:
        call_func = call.data.split(' ')
        if len(call_func) > 1:
            if call_func[0] in call_list:
                func_menu = Menu_Dict[call_func[0]]
                func_menu(update, context, call_func[1])
        else:
            func_menu = Menu_Dict[call.data]
            func_menu(update, context)
    # Если сообщение из инлайн-режима
    # elif call.inline_message_id:
    #	func_menu = Menu_Dict[call.data]
    #	func_menu(call, context)

# Удаляем записи для отображения только одной


# функция удаляющая предыдущие сообщения бота (делает эффект обновления меню при нажатии кнопки) и человека по States.S_MENU(всегда, если его статус=1)
def del_mes(update: Update, context: CallbackContext, bot_msg: bool = False):
    message = get_message_bot(update)
    try:
        context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    if bot_msg:
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-1)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-2)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-3)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-4)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-5)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-6)
        except:
            pass

# Распаковываем message


def get_message_bot(update):
    if hasattr(update, 'message') and update.message != None:
        message = update.message
    if hasattr(update, 'callback_query') and update.callback_query != None:
        message = update.callback_query.message
    return message

# Проверяем является ли float


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

#{'user': {'id': 1821543506, 'last_name': 'Абрамова', 'is_bot': False, 'first_name': 'Алла', 'language_code': 'ru', 'username': 'abralalalaa'}, 'status': 'left', 'until_date': None}

def check_in(update: Update, context: CallbackContext, chat_id: int|str = -1001606481866):
    message = get_message_bot(update)
    u = User.get_user(update, context)
    check_in_user = context.bot.get_chat_member(chat_id=chat_id, user_id=u.user_id)
    print(check_in_user)
    if hasattr(check_in_user, 'status') and (check_in_user.status == 'left' or check_in_user.status == 'kicked'):# 'left' 'member' 'kicked'
        u.state = static_state.S_CHECK_IN
        id = context.bot.send_message(message.chat.id, static_text.NOT_CHACK_IN, reply_markup=make_keyboard_for_check_in())  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
        return False
    return True


# Проверка на username


def check_username(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    if not hasattr(message.chat, 'username') or message.chat.username == '' or message.chat.username == None:
        u = User.get_user(update, context)
        u.state = static_state.S_USERNAME
        id = context.bot.send_message(message.chat.id, static_text.NOT_USER_NAME.format(
            text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_in())  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
        return False
    return True

# Проверка на email
def change_email(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    u, _ = User.get_user_and_created(update, context)
    u.state = static_state.S_EMAIL
    id = context.bot.send_message(message.chat.id, static_text.NOT_EMAIL_NAME.format(
        text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_username())  # отправляет приветствие и кнопку
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def check_email(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    u, _ = User.get_user_and_created(update, context)
    if u.email == '' or u.email == None:
        u = User.get_user(update, context)
        u.state = static_state.S_EMAIL
        id = context.bot.send_message(message.chat.id, static_text.NOT_EMAIL_NAME.format(
            text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_username())  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
        return False
    return True

def s_email(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    email = message.text
    try:
        u.email = email
        u.state = static_state.S_MENU
        u.save()
    except:
        del_mes(update, context, True)
        return check_email(update, context)
# Начало диалога


def command_start(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    url = ''
    t = {}
    if context is not None and context.args is not None and len(context.args) > 0:
        payload = context.args[0]
        if not is_number(payload):
            try:
                camp = Campaign.objects.get(bot_url=payload)
                name = camp.name
                url = camp.target_url
                t = loads(camp.comment.replace("\'", ""))
                h, h_created = History.objects.get_or_create(name=name, user_id=u, is_repeat=False, defaults={
                    'bot_url': camp
                })
                if not h_created:
                    History.objects.create(name=name, user_id=u, bot_url=camp, is_repeat=True)
            except:
                pass
    # if check_in(update, context):
        # if u.state == static_state.S_ACCEPTED_ORDER:
        #     cmd_accepted_order_show(update, context)
        #     return
        # if u.state == static_state.S_USERNAME:
        #     cmd_wallet(update, context)
        #     del_mes(update, context, True)
        #     return
    text = '\n'
    u.state = static_state.S_MENU
    print(t)
    print('photo' in t)
    if 'photo' in t and t['photo'] != None and len(t['photo']) > 0:
        entities = _from_celery_entities_to_entities(t['caption_entities'])
        id = context.bot.send_photo(
                chat_id=message.chat.id, photo=t['photo'][-1]['file_id'], caption=t['caption'] if 'caption' in t else None, caption_entities=entities, reply_markup=make_keyboard_for_start(url = url))
    if 'text' in t and t['text'] != None  and len(t['text']) > 0 and t['text'] != '_':
        entities = _from_celery_entities_to_entities(t['entities'])
        id = context.bot.send_message(
            message.chat.id, t['text'], entities=entities, reply_markup=make_keyboard_for_start(url = url), disable_web_page_preview=True)
    if (not 'photo' in t and not 'text' in t) or ('text' in t and t['text'] != None  and len(t['text']) > 0 and t['text'] == '_'):
        id = context.bot.send_message(message.chat.id, static_text.START_USER.format(
            text=text), reply_markup=make_keyboard_for_start(url=url), parse_mode="HTML")  # отправляет приветствие и кнопку
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

    # if created:
    #     text = static_text.start_created.format(first_name=u.first_name)
    # else:
    #     text = static_text.start_not_created.format(first_name=u.first_name)

    # update.message.reply_text(text=text, reply_markup=make_keyboard_for_start_command())


# Меню


def cmd_menu(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    # if check_in(update, context):
        # помечаем состояние пользователя.
    u.state = static_state.S_MENU
    admin_menu = False
    if u.is_admin or u.is_moderator:
        admin_menu = True
    id = context.bot.send_message(
        message.chat.id, static_text.MENU, reply_markup=make_keyboard_for_cmd_menu(admin_menu), parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)




###################################
###################################
def cmd_help(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    # u.state = static_state.S_MENU_HELP
    id = context.bot.send_message(
        message.chat.id, static_text.HELP,
        reply_markup=make_keyboard_for_cmd_help(), parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def s_help(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    u.state = static_state.S_MENU_HELP
    temp = dumps(message.to_dict())
    t = loads(temp)
    if hasattr(message, 'photo') and message.photo != None and len(message.photo) > 0:
        entities = _from_celery_entities_to_entities(t['caption_entities'])
        id = context.bot.send_photo(
                chat_id=message.chat.id, photo=message.photo[-1]['file_id'], caption=message.caption, caption_entities=entities, reply_markup=make_keyboard_for_start(url = 'https://t.me/Your_bot?start=1821543506'))#make_keyboard_for_cmd_help())
    if hasattr(message, 'text') and message.text != None  and len(message.text) > 0:
        entities = _from_celery_entities_to_entities(t['entities'])
        id = context.bot.send_message(
            message.chat.id, t['text'], entities=entities,
            reply_markup=make_keyboard_for_cmd_help(), disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)


def cmd_admin(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        u.state = static_state.S_MENU_ADMIN
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_MENU_TEXT.format(''), reply_markup=make_keyboard_for_cmd_admin(u.is_admin), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def cmd_assign_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if u.is_admin:
        u.state = static_state.S_ASSIGN_CAMP_NAME
        camp_query = History.objects.order_by().values_list('name', flat=True).distinct('name')
        camps = ''
        for c_q in camp_query:
            camps += f'<code>{c_q}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ASSIGN_CAMP_NAME.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_assign_camp_name(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin:
        message = get_message_bot(update)
        u.dict = dumps(dict(name=message.text.strip()))
        u.state = static_state.S_ASSIGN_CAMP_USER
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ASSIGN_CAMP_USER.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def s_assign_camp_user(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        if hasattr(message, 'text') and message.text[0] == '@':
            user_ = message.text.strip().split(' ')[0]
        elif hasattr(message, 'forward_from') and hasattr(message.forward_from, 'id') and message.forward_from.id > 0:
            user_ = message.forward_from.id
        else:
            return cmd_assign_camp(update, context, 'Пользователь не найден, попробуй еще раз...')
        try:
            f_u = User.get_user_by_username_or_user_id(user_)
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            f_u.dict = dumps(dict(name=temp.name))
            f_u.is_moderator = not f_u.is_moderator
            f_u.save()
        except:
            return cmd_assign_camp(update, context, 'Пользователь не найден, попробуй еще раз...')
        u.state = static_state.S_CHECK_SET_SUMM
        text = f'разжалован из модераторов кампании {temp.name}'
        if f_u.is_moderator:
            text = f'назначен модератором кампании {temp.name}'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ASSIGN_CAMP_USER_READY.format(f_u, text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def cmd_add_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if u.is_moderator:
        u.state = static_state.S_ADD_CAMP_BOT_URL
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_BOT_URL.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        return
    if u.is_admin:
        u.state = static_state.S_ADD_CAMP_NAME
        camp_query = Campaign.objects.order_by().values_list('name', flat=True).distinct('name')
        camps = ''
        for c_q in camp_query:
            camps += f'<code>{c_q}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
        return
    else:
        command_start(update, context)

def s_add_camp_name(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin:
        message = get_message_bot(update)
        try:
            u.dict = dumps(dict(name=message.text.strip()))
        except:
            return cmd_add_camp(update, context, 'Не получилось записать название кампании, попробуй покороче')
        u.state = static_state.S_ADD_CAMP_BOT_URL
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_BOT_URL.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def s_add_camp_bot_url(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        try:
            bot_url = message.text.strip()
            if len(bot_url) <= 64 and len(bot_url) > 0:
                temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
                temp.bot_url = bot_url
                u.dict = dumps(temp.__dict__)
                u.state = static_state.S_ADD_CAMP_TARGET_URL
                id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_TARGET_URL.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
                u.message_id = id.message_id
                u.save()
                del_mes(update, context, True)
            else:
                return cmd_add_camp(update, context, 'Слишком длинная ссылка. Начинаем с начала')
        except:
            return cmd_add_camp(update, context, 'Не удалось сохранить ссылку')
    else:
        command_start(update, context)

def s_add_camp_target_url(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        try:
            target_url = message.text.strip()
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            temp.target_url = target_url
            u.dict = dumps(temp.__dict__)
            u.state = static_state.S_ADD_CAMP_COMMENT
            id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_COMMENT.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
            u.message_id = id.message_id
            u.save()
            del_mes(update, context, True)
        except:
            return cmd_add_camp(update, context, 'Не удалось сохранить ссылку')
    else:
        command_start(update, context)

def s_add_camp_comment(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    u.state = static_state.S_ADD_CAMP_AD_COST
    temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
    temp.comment = dumps(message.to_dict())
    t = loads(temp.comment)
    if hasattr(message, 'photo') and message.photo != None and len(message.photo) > 0:
        entities = _from_celery_entities_to_entities(t['caption_entities'])
        id = context.bot.send_photo(
                chat_id=message.chat.id, photo=t['photo'][-1]['file_id'], caption=message.caption, caption_entities=entities, reply_markup=make_keyboard_for_start(url = temp.target_url))
    if hasattr(message, 'text') and message.text != None and message.text != '_'  and len(message.text) > 0:
        entities = _from_celery_entities_to_entities(t['entities'])
        id = context.bot.send_message(
            message.chat.id, t['text'], entities=entities, reply_markup=make_keyboard_for_start(url = temp.target_url), disable_web_page_preview=True)
    if hasattr(message, 'text') and message.text == '_':
        temp.comment = {}
        id = context.bot.send_message(message.chat.id, static_text.START_USER.format(
            text=text), reply_markup=make_keyboard_for_start(url=temp.target_url), parse_mode="HTML")  # отправляет приветствие и кнопку'
    u.dict = dumps(temp.__dict__)
    id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_AD_COST.format(text), reply_markup=make_keyboard_for_admin_menu_change(), parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def cmd_change_post(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    u.state = static_state.S_ADD_CAMP_COMMENT
    id = context.bot.send_message(message.chat.id, static_text.ADMIN_ADD_CAMP_COMMENT.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def s_add_camp_ad_cost(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        try:
            summ = float(message.text.strip())
            temp = loads(u.dict)
            t = temp['comment']
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            temp.ad_cost = summ
        except:
            return cmd_add_camp(update, context, 'Это не цифра, попробуй еще раз сначала.')
        Campaign.objects.create(name=temp.name,
            bot_url=temp.bot_url, 
            target_url=temp.target_url,
            ad_cost=temp.ad_cost,
            comment=t
        )#{dumps(temp.__dict__)}
        return cmd_add_camp(update, context, f'Данные сохранены.\nСсылка для рекламы:\n<code>https://t.me/Trafficcontrol_bot?start={temp.bot_url}</code>')
    else:
        command_start(update, context)

def cmd_сh_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        u.state = static_state.S_СH_CAMP
        if u.is_admin:
            camp_query = Campaign.objects.order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        else:
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            camp_query = Campaign.objects.filter(name=temp.name).order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        camps = ''
        for c_n, c_u in camp_query:
            camps += f'<code>{c_n} {c_u}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_СH_CAMP.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_сh_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        name, bot_url = message.text.strip().split(' ')
        u.state = static_state.S_СH_CAMP_AD_COST
        u.dict = dumps(dict(name=name, bot_url=bot_url))
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_СH_CAMP_AD_COST.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_сh_camp_ad_cost(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        u.state = static_state.S_MENU_ADMIN
        try:
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            summ = float(message.text)
            camp = Campaign.objects.get(name=temp.name, bot_url=temp.bot_url)
            camp.ad_cost = summ
            camp.save()
            if text == '':
                text += f"Кампания: <code>{temp.name} {temp.bot_url}</code> сумма изменена."
        except:
            text += f"это не цифра"
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_СH_CAMP_AD_COST_READY.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def cmd_my_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        u.state = static_state.S_MENU_ADMIN
        if u.is_admin:
            camp_query = Campaign.objects.order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        else:
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            camp_query = Campaign.objects.filter(name=temp.name).order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        camps = ''
        for c_n, c_u in camp_query:
            camps += f'{c_n} <code>https://t.me/Trafficcontrol_bot?start={c_u}</code>\n'
        id = context.bot.send_message(message.chat.id, camps, reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def cmd_del_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        u.state = static_state.S_DEL_CAMP
        if u.is_admin:
            camp_query = Campaign.objects.order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        else:
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            camp_query = Campaign.objects.filter(name=temp.name).order_by().values_list('name', 'bot_url').distinct('name','bot_url')
        camps = ''
        for c_n, c_u in camp_query:
            camps += f'<code>{c_n} {c_u}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_DEL_CAMP.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_del_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        name, bot_url = message.text.strip().split(' ')
        u.state = static_state.S_MENU_ADMIN
        try:
            Campaign.objects.filter(name=name, bot_url=bot_url).delete()
            History.objects.filter(name=name, bot_url=bot_url).delete()
            if text == '':
                text += f"Кампания: <code>{name} {bot_url}</code> удалена."
        except:
            text += f"Кампания: <code>{name} {bot_url}</code> не существует."
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_DEL_CAMP_READY.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def cmd_stat_camp(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_moderator:
        s_stat_camp_name(update, context)
        return
    if u.is_admin:
        message = get_message_bot(update)
        u.state = static_state.S_STAT_CAMP_NAME
        camp_query = Campaign.objects.order_by().values_list('name', flat=True).distinct('name')
        camps = ''
        for c_n in camp_query:
            camps += f'<code>{c_n}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_STAT_CAMP.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
        return
    else:
        command_start(update, context)

def s_stat_camp_name(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        if u.is_admin:
            name = message.text.strip()
            camp_query = History.objects.filter(name=name).values()
        else:
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            name = temp.name
            camp_query = History.objects.filter(name=name).values()
        csv_camp = _get_csv_from_qs_values(camp_query)
        u.state = static_state.S_MENU_ADMIN
        campaign_bot_url = Campaign.objects.filter(name=name).order_by().values_list('name','bot_url', 'ad_cost').distinct('bot_url')
        for name, bot_url, ad_cost in campaign_bot_url:
            try:
                summ = float(History.objects.filter(name=name, bot_url=bot_url).aggregate(Sum('total_profit'))['total_profit__sum'])
                count_users = History.objects.filter(name=name, bot_url=bot_url).exclude(is_repeat=True).count()
            except:
                summ = 0
                count_users = 0
            price_user = 0
            if count_users > 0 and ad_cost > 0:
                price_user = ad_cost / count_users
            percent = 0
            if summ > 0 and ad_cost > 0:
                percent = summ / ad_cost * 100
            text += f"<code>Кампания: {name} {bot_url} Потрачено {ad_cost} Подписчики {count_users} Цена за подписчика {price_user} Доход {summ} Окупаемость % {percent}</code>\n\n"
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_STAT_CAMP_READY.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        context.bot.send_document(chat_id=u.user_id, document=csv_camp)
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def cmd_check_user(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if u.is_moderator:
        u.state = static_state.S_CHECK_MESSAGE
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_CHECK_USER.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
    if u.is_admin:
        u.state = static_state.S_CHECK_CAMP_NAME
        camp_query = History.objects.order_by().values_list('name', flat=True).distinct('name')
        camps = ''
        for c_q in camp_query:
            camps += f'<code>{c_q}</code>\n'
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_CHECK_CAMP_USER.format(text, camps), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_check_camp_name(update: Update, context: CallbackContext, text = ''):
    u = User.get_user(update, context)
    if u.is_admin:
        message = get_message_bot(update)
        u.dict = dumps(dict(name=message.text.strip()))
        u.state = static_state.S_CHECK_MESSAGE
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_CHECK_USER.format(text), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def s_check_user(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        try:
            f_u = User.objects.get(user_id=message.forward_from.id)
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            temp.user_id = message.forward_from.id
            u.dict = dumps(temp.__dict__)
        except:
            return cmd_check_user(update, context, 'Пользователь не найден, попробуй еще раз...')
        u.state = static_state.S_CHECK_SET_SUMM
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_CHECK_SET_SUMM.format(f_u), reply_markup=make_keyboard_for_admin_menu(), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def s_check_set_summ(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin or u.is_moderator:
        message = get_message_bot(update)
        try:
            summ = float(message.text.strip())
            temp = loads(u.dict, object_hook=lambda d: SimpleNamespace(**d))
            h_u = History.objects.get(name=temp.name, user_id=temp.user_id, is_repeat=False)
            h_u.total_profit += summ
            h_u.save()
        except:
            return cmd_check_user(update, context, 'Это не цифра, попробуй еще раз сначала.')
        return cmd_check_user(update, context, 'Доход пользователя изменен')
    else:
        command_start(update, context)


def cmd_pass():
    pass


# словарь функций Меню по состоянию
State_Dict = {
    # Когда выбрано Меню, мы можем только нажимать кнопки. Любой текст удаляется
    static_state.S_MENU: del_mes,
    static_state.S_CHECK_CAMP_NAME: s_check_camp_name,
    static_state.S_CHECK_MESSAGE: s_check_user,
    static_state.S_CHECK_SET_SUMM: s_check_set_summ,
    static_state.S_ADD_CAMP_NAME: s_add_camp_name,
    static_state.S_ADD_CAMP_BOT_URL: s_add_camp_bot_url,
    static_state.S_ADD_CAMP_TARGET_URL: s_add_camp_target_url,
    static_state.S_ADD_CAMP_COMMENT: s_add_camp_comment,
    static_state.S_ADD_CAMP_AD_COST: s_add_camp_ad_cost,
    static_state.S_STAT_CAMP_NAME: s_stat_camp_name,
    static_state.S_DEL_CAMP: s_del_camp,
    static_state.S_СH_CAMP: s_сh_camp,
    static_state.S_СH_CAMP_AD_COST: s_сh_camp_ad_cost,
    static_state.S_ASSIGN_CAMP_NAME: s_assign_camp_name,
    static_state.S_ASSIGN_CAMP_USER: s_assign_camp_user,
}

# словарь функций Меню
Menu_Dict = {
    'Старт': command_start,
    'Меню': cmd_menu,
    'Почта': change_email,
    'Администрирование': cmd_admin,
    'Назначить_кампанию': cmd_assign_camp,
    'Изменить_сумму': cmd_сh_camp,
    'Мои_кампании': cmd_my_camp,
    'Добавить_кампанию': cmd_add_camp,
    'изменить_пост': cmd_change_post,
    'Чек_пользователя': cmd_check_user,
    'Выгрузить_статистику': cmd_stat_camp,
    'Удалить_кампанию': cmd_del_camp,
    'pass': cmd_pass,
    'Help': cmd_help,
}