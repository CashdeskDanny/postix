# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-14 15:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20160618_2216'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='receipt_name',
            field=models.CharField(default='receipt_name', max_length=28),
            preserve_default=False,
        ),
    ]