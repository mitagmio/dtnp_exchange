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
from analytic.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


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
    is_blocked_bot = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()
    dict = models.TextField(**nb)

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
                    u.deep_link = payload
                    u.save()

        return u, created


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


class Campaign (CreateTracker):
    name = models.CharField(max_length=256)
    bot_url = models.CharField(max_length=64, primary_key=True)
    target_url = models.CharField(max_length=256, **nb)
    ad_cost = models.FloatField(default=0)
    comment = models.TextField(**nb)


class History (CreateTracker):
    name = models.CharField(max_length=256)
    bot_url = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='history_camp_set')
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='history_user_set')
    total_profit = models.FloatField(default=0)
    is_repeat = models.BooleanField(default=False)
