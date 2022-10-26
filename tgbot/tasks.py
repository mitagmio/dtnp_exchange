"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from datetime import datetime
from typing import Union, List, Optional, Dict

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.models import Settings, User, Invoice, History
from analytic.models import History as his

from dtb.celery import app
from celery.utils.log import get_task_logger
from tgbot.handlers.broadcast_message.utils import _send_message, _del_message, \
    _from_celery_entities_to_entities, _from_celery_markup_to_markup

from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
def broadcast_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = _from_celery_entities_to_entities(entities)
    reply_markup_ = _from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            _send_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")

@app.task(ignore_result=True)
def payment() -> None:
    """ Подтверждаем оплату по выставленным счетам  """
    logger.info("Starting payment invoices")
    settings = Settings.objects.get(id=1)
    timeblock = 0
    Users = User.objects.exclude(addr='0')
    logger.info(
        f"min_timestamp {int(settings.last_time_payment)}")
    try:
        client = Tron(provider=HTTPProvider(api_key=[settings.key1, settings.key2, settings.key3]), network='mainnet')
        contract = client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') #usdt
    except Exception as e:
        print('Error Client or Contract', e)
        pass
    for u in Users:
        try:
            print(u.username, u.addr)
            Transactions = Invoice.get_payment(
                int(settings.last_time_payment),
                str(u.addr)
                )['data']
            logger.info(
                f"Transactions {Transactions}")
        except Exception as e:
            Transactions = dict()
            logger.info(
                f"Transactions {len(Transactions)}, reason: {e}")
        if len(Transactions) > 0:

            for t in Transactions:
                if int(t['block_timestamp']) > timeblock:
                    timeblock = int(t['block_timestamp'])
                pay_value = float(0.0)
                if t['to'] == str(u.addr) and t['token_info']['symbol']=='USDT':
                    pay_value = float(t['value']) / \
                        10**float(t['token_info']['decimals'])

                # try:
                #     inv = Invoice.objects.get(summ_invoice=pay_value)
                # except Invoice.DoesNotExist:
                #     inv = None
                # if inv != None:
                    # u = inv.payer_id
                if pay_value > 0 :
                    ref_accrual = False
                    if pay_value < 1000:
                        inv = 0
                        u.balance_withdrawal += pay_value
                        if u.balance_withdrawal >= 1000:
                            new_bal = int(u.balance_withdrawal / 1000) * 1000
                            u.balance_withdrawal -= new_bal
                            u.balance += new_bal
                            if u.balance > u.max_invest:
                                u.max_invest += new_bal
                                ref_accrual = True
                            text = '💵 Ваш платеж на сумму <code>{}</code>$ зачислен.\n\nТекущий баланс для вывода составляет: <code>{}</code>$\n\nВсего инвестированно: <code>{}</code>$'.format(
                            pay_value, u.balance_withdrawal,  u.balance)
                        else:
                            text = '💵 Ваш платеж на сумму <code>{}</code>$ зачислен.\n\nТекущий баланс для вывода составляет: <code>{}</code>$'.format(
                                pay_value, u.balance_withdrawal)
                        History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u)
                        time.sleep(0.1)
                    if pay_value >= 1000:
                        inv = 0
                        new_bal = int(pay_value /1000)*1000
                        u.balance += new_bal
                        inv += new_bal
                        u.balance_withdrawal += pay_value - new_bal
                        if u.balance_withdrawal >= 1000:
                            new_bal = int(u.balance_withdrawal / 1000) * 1000
                            u.balance_withdrawal -= new_bal
                            u.balance += new_bal
                            if u.balance > u.max_invest:
                                u.max_invest += new_bal
                            inv += new_bal
                        text = '💵 Ваш платеж на сумму <code>{}</code>$ зачислен.\n\nТекущий баланс для вывода составляет: <code>{}</code>$\n\nВсего инвестированно: <code>{}</code>$'.format(
                            pay_value, u.balance_withdrawal,  u.balance)
                        History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u)
                        time.sleep(0.1)
                    try:
                        if ref_accrual:
                            if u.ref_1_id.user_id > 0:
                                ref_summ = inv * 0.1
                                u.ref_1_id.funds_raised_ref_1 += inv
                                u.ref_1_id.balance_withdrawal += ref_summ
                                u.ref_1_id.reward_ref_1 += ref_summ
                                u.ref_1_id.save()
                                text = '💵 Вам произведено начисление {ref_summ}$ за Реферала 1 уровня и сумма {balance_withdrawal}$ доступна к выводу.'.format(ref_summ=ref_summ, balance_withdrawal=u.ref_1_id.balance_withdrawal)
                                _send_message(
                                    user_id=u.ref_1_id.user_id,
                                    text=text,
                                    entities=None,
                                    parse_mode=telegram.ParseMode.HTML,
                                    reply_markup=None,
                                )
                                History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u.ref_1_id)
                                time.sleep(0.1)
                            u.ref_2_id = u.ref_1_id.ref_1_id
                            if u.ref_2_id.user_id > 0:
                                ref_summ = inv * 0.05
                                u.ref_2_id.funds_raised_ref_2 += inv
                                u.ref_2_id.balance_withdrawal += ref_summ
                                u.ref_2_id.reward_ref_2 += ref_summ
                                u.ref_2_id.save()
                                text = '💵 Вам произведено начисление {ref_summ}$ за Реферала 2 уровня и сумма {balance_withdrawal}$ доступна к выводу.'.format(ref_summ=ref_summ, balance_withdrawal=u.ref_2_id.balance_withdrawal)
                                _send_message(
                                    user_id=u.ref_2_id.user_id,
                                    text=text,
                                    entities=None,
                                    parse_mode=telegram.ParseMode.HTML,
                                    reply_markup=None,
                                )
                                History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u.ref_2_id)
                                time.sleep(0.1)
                            u.ref_3_id = u.ref_1_id.ref_1_id.ref_1_id
                            if u.ref_3_id.user_id > 0:
                                ref_summ = inv * 0.03
                                u.ref_3_id.funds_raised_ref_3 += inv
                                u.ref_3_id.balance_withdrawal += ref_summ
                                u.ref_3_id.reward_ref_3 += ref_summ
                                u.ref_3_id.save()
                                text = '💵 Вам произведено начисление {ref_summ}$ за Реферала 3 уровня и сумма {balance_withdrawal}$ доступна к выводу.'.format(ref_summ=ref_summ, balance_withdrawal=u.ref_3_id.balance_withdrawal)
                                _send_message(
                                    user_id=u.ref_3_id.user_id,
                                    text=text,
                                    entities=None,
                                    parse_mode=telegram.ParseMode.HTML,
                                    reply_markup=None,
                                )
                                History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u.ref_3_id)
                                time.sleep(0.1)
                    except:
                        pass
                    _send_message(
                        user_id=u.user_id,
                        text=text,
                        entities=None,
                        parse_mode=telegram.ParseMode.HTML,
                        reply_markup=None,
                    )
                    time.sleep(0.5)
                    _send_message(
                        user_id=-1001793015412,
                        text='💵 Поступил платеж на сумму <code>{}</code> от @{}'.format(pay_value, u.username),
                        entities=None,
                        parse_mode=telegram.ParseMode.HTML,
                        reply_markup=None,
                    )
                    # inv.delete()
                u.hot_balance_usdt += pay_value # contract.functions.balanceOf(str(u.addr))/10**float(contract.functions.decimals())
                try:
                    u.hot_balance_trx = float(client.get_account_balance(str(u.addr)))
                    time.sleep(1.5)
                    if u.hot_balance_trx > 0 and u.hot_balance_trx < 20:
                        fee = float(20 - u.hot_balance_trx)
                except Exception as e:
                    print('Error Get balance TRX', e)
                    fee = float(20)
       
                if u.hot_balance_trx == 0:
                    fee = float(20)

                if u.hot_balance_trx >= 20:
                    fee = 0
                
                try:
                    if fee > 0:    
                        giver = User.objects.get(user_id=2076920918)
                        priv_key = PrivateKey(bytes.fromhex(giver.private_key))
                        txn = (
                            client.trx.transfer(giver.addr, u.addr, int(fee*1000000))
                            .build()
                            .sign(priv_key)
                        )
                        txn.broadcast().wait(timeout=60, interval=1.8)
                        u.hot_balance_trx += fee
                except Exception as e:
                    print('Error Send TRX from giver wallet', e)

                # try:        
                #     if fee == 0:
                #         priv_key = PrivateKey(bytes.fromhex(u.private_key))
                #         txn = (
                #             contract.functions.transfer('THKqtdfNBxqkSwzLTV9JMANgW9p1uZBDN4', int(pay_value*1000000))
                #             .with_owner(u.addr) # address of the private key
                #             .fee_limit(20_000_000)
                #             .build()
                #             .sign(priv_key)
                #         )
                #         txn.broadcast().wait(timeout=60, interval=1.8)
                # except Exception as e:
                #     print('Error Send to treasure wallet', e)
            u.save()
        time.sleep(1.5)
    if timeblock > settings.last_time_payment:
        settings.last_time_payment = timeblock + 1000
        settings.save()
    logger.info("Payment invoices was completed!")

@app.task(ignore_result=True)
def send_to_treasure() -> None:
    """ Отправляем в хранилище  """
    logger.info("Starting send to treasure")
    Users = User.objects.filter(hot_balance_trx__gt=0).filter(hot_balance_usdt__gt=0)
    try:
        len_u = len(Users)
    except:
        len_u = 0
    if len_u > 0:
        settings = Settings.objects.get(id=1)
        try:
            client = Tron(provider=HTTPProvider(api_key=[settings.key1, settings.key2, settings.key3]), network='mainnet')
            contract = client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') #usdt
        except Exception as e:
            print('Error Client or Contract', e)
            pass
        for u in Users:
            try:
                priv_key = PrivateKey(bytes.fromhex(u.private_key))
                txn = (
                    contract.functions.transfer('TWKe8uGQpARMi3ejmdvd9UP9kh8sXT4C3x', int(u.hot_balance_usdt*1000000))
                    .with_owner(u.addr) # address of the private key
                    .fee_limit(20_000_000)
                    .build()
                    .sign(priv_key)
                )
                txn.broadcast().wait(timeout=60, interval=1.8)
                u.hot_balance_usdt = 0
                time.sleep(2)
                u.hot_balance_trx = float(client.get_account_balance(str(u.addr)))
            except Exception as e:
                print('Error Send to treasure wallet', e)
                pass
            u.save()
        giver = User.objects.get(user_id=2076920918)
        giver.hot_balance_trx = float(client.get_account_balance(str(giver.addr)))
        giver.save()
        if giver.hot_balance_trx <= 200:
            _send_message(
                user_id=2076920918,
                text='💵 TRX для комиссии осталось меньше чем на 10 переводов. Пополни пожалуйста кошелек в боте.',
                entities=None,
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=None,
            )
    logger.info("Send to treasure was completed!")

@app.task(ignore_result=True)
def percentage_everyday() -> None:
    """ Начисляем проценты  """
    logger.info("Starting send percentage")
    Users = User.objects.filter(balance__gte=1000)
    try:
        len_u = len(Users)
    except:
        len_u = 0
    if len_u > 0:
        for u in Users:
            u.total_profit += u.balance * 0.03
            u.save()
    logger.info("Send percentage was completed!")

@app.task(ignore_result=True)
def percentage_to_withdraw() -> None:
    """ Начисляем проценты в баланс для вывода  """
    logger.info("Starting send percentage")
    Users = User.objects.filter(total_profit__gt=0)
    try:
        len_u = len(Users)
    except:
        len_u = 0
    if len_u > 0:
        for u in Users:
            total_profit = u.total_profit
            u.balance_withdrawal += total_profit
            u.total_profit = 0
            u.save()
            text = '💵 Вам произведено начисление {total_profit}$ за неделю и сумма {balance_withdrawal}$ доступна к выводу.'.format(total_profit=total_profit, balance_withdrawal=u.balance_withdrawal)
            _send_message(
                user_id=u.user_id,
                text=text,
                entities=None,
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=None,
            )
            History.objects.create(timestamp=int(datetime.today().timestamp()), comment=text, user_id=u)
    logger.info("Send percentage was completed!")

@app.task(ignore_result=True)
def write_check_p2p_to_trafc() -> None:
    """ Начисляем проценты в баланс для вывода  """
    logger.info("Starting send percentage")
    Users = his.objects.filter(name='p2p').exclude(is_repeat=True)
    try:
        len_u = len(Users)
    except:
        len_u = 0
    if len_u > 0:
        for h in Users:
            u = User.objects.get(user_id=h.user_id_id)
            h.total_profit = u.total_profit
            h.save()
    logger.info("Send percentage was completed!")

