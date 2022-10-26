from __future__ import annotations

from typing import List, Union, Optional, Tuple, Dict
import hmac
import time
import hashlib
import base64
import requests
from requests.structures import CaseInsensitiveDict
from urllib.parse import urlencode
from datetime import datetime

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from dtb.settings import DEBUG
from tgbot.handlers.utils.info import extract_user_data_from_update, gen_addr_priv
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class Settings(models.Model):
    last_time_payment = models.PositiveBigIntegerField(default=1651688047000)
    key1 = models.CharField(max_length=256, **nb)
    key2 = models.CharField(max_length=256, **nb)
    key3 = models.CharField(max_length=256, **nb)

    @classmethod
    def get_dict(cls) -> Dict:
        settings = list(cls.objects.all().values())
        dict_settings = {}
        for el in settings:
            dict_settings['last_time_payment'] = el['last_time_payment']
        return dict_settings


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(
        max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    state = models.CharField(max_length=32, default='0')
    message_id = models.PositiveBigIntegerField(default=0)
    balance = models.FloatField(default=0)
    balance_withdrawal = models.FloatField(default=0)
    total_profit = models.FloatField(default=0)
    addr = models.CharField(max_length=256, default='0')
    addr_hex = models.CharField(max_length=256, **nb)
    public_key = models.CharField(max_length=256, **nb)
    private_key = models.CharField(max_length=256, **nb)
    hot_balance_trx = models.FloatField(default=0)
    hot_balance_usdt = models.FloatField(default=0)
    is_blocked_bot = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    email = models.CharField(max_length=256, **nb)
    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()
    ref_1_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name='ref_1_id_user_set', **nb)
    ref_2_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name='ref_2_id_user_set', **nb)
    ref_3_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name='ref_3_id_user_set', **nb)
    count_ref_1 = models.IntegerField(default=0)
    count_ref_2 = models.IntegerField(default=0)
    count_ref_3 = models.IntegerField(default=0)
    funds_raised_ref_1 = models.FloatField(default=0)
    funds_raised_ref_2 = models.FloatField(default=0)
    funds_raised_ref_3 = models.FloatField(default=0)
    reward_ref_1 = models.FloatField(default=0)
    reward_ref_2 = models.FloatField(default=0)
    reward_ref_3 = models.FloatField(default=0)
    max_invest = models.FloatField(default=0)

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(
            user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                # you can't invite yourself
                if str(payload).strip() != str(data["user_id"]).strip():
                    try:
                        u.ref_1_id = User.objects.get(user_id=int(str(payload).strip()))
                        if u.ref_1_id.user_id > 0:
                            u.ref_1_id.count_ref_1 += 1
                            u.ref_1_id.save()
                        u.ref_2_id = u.ref_1_id.ref_1_id
                        if u.ref_2_id.user_id > 0:
                            u.ref_2_id.count_ref_2 += 1
                            u.ref_2_id.save()
                        u.ref_3_id = u.ref_1_id.ref_1_id.ref_1_id
                        if u.ref_3_id.user_id > 0:
                            u.ref_3_id.count_ref_3 += 1
                            u.ref_3_id.save()
                    except:
                        pass
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def set_user_addr(cls, update: Update, context: CallbackContext):
        """ set user addr """
        u, _ = cls.get_user_and_created(update, context)
        try:
            if u.addr == '0':
                u.addr, u.addr_hex, u.public_key, u.private_key = gen_addr_priv()
                print(f'{u} {u.user_id} Save addr {u.addr}, addr_hex {u.addr_hex}, public_key {u.public_key}, private_key {u.private_key}')
                u.save()
        except Exception as e:
            print('Error save addr', e)
        return u

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"

class Invoice (models.Model):
    summ_invoice = models.FloatField(primary_key=True)
    payer_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payer_id_invoice_set')

    @staticmethod
    def get_payment(min_timestamp: int, address: str) -> Dict:
        url = "https://api.trongrid.io/v1/accounts/"+address+"/transactions/trc20?limit=20&contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&only_confirmed=true&min_timestamp={}".format(
            min_timestamp)
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        r = requests.get(url, headers=headers)
        print(f"status code = {r.status_code}")
        return r.json()

class History (CreateTracker):
    timestamp = models.PositiveBigIntegerField(primary_key=True)
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='history_set')
    comment = models.TextField(**nb)

class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)
        # Parse location with arcgis
        from arcgis.tasks import save_data_from_arcgis
        if DEBUG:
            save_data_from_arcgis(latitude=self.latitude,
                                  longitude=self.longitude, location_id=self.pk)
        else:
            save_data_from_arcgis.delay(
                latitude=self.latitude, longitude=self.longitude, location_id=self.pk)
