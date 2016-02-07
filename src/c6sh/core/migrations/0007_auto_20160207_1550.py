# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-07 14:50
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20160207_1208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listconstraintproduct',
            name='upgrade_products',
        ),
        migrations.RemoveField(
            model_name='warningconstraintproduct',
            name='upgrade_products',
        ),
        migrations.AddField(
            model_name='listconstraintproduct',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='listconstraintproduct',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
        migrations.AddField(
            model_name='warningconstraintproduct',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='warningconstraintproduct',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
    ]