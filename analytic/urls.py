from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from dtb.settings import TELEGRAM_WEBHOOK_SECRET_2
from . import views

urlpatterns = [  
    path(TELEGRAM_WEBHOOK_SECRET_2, csrf_exempt(views.TelegramBotWebhookView.as_view())), # default TELEGRAM_WEBHOOK='super_secter_webhook/'
]