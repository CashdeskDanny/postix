# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-26 22:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_eventsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventsettings',
            name='report_footer',
            field=models.CharField(default='CCCV Veransstaltungsgesellschaft mbH', help_text='This will show up on backoffice session reports.', max_length=500),
        ),
    ]
