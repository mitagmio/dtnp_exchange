# Generated by Django 3.2.13 on 2022-07-12 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0008_auto_20220705_0626'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='max_invest',
            field=models.FloatField(default=0),
        ),
    ]
