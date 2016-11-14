import glob
import os
import random
import string
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Union

from django.core.files.storage import default_storage
from django.db import models
from django.utils.timezone import now

from ..utils.displays import DummyDisplay, OverheadDisplay
from ..utils.printing import CashdeskPrinter, DummyPrinter
from .base import Item, Product, TransactionPosition, TransactionPositionItem
from .settings import EventSettings


def generate_key() -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for i in range(32))


class Cashdesk(models.Model):
    name = models.CharField(max_length=254)
    ip_address = models.GenericIPAddressField(unique=True, verbose_name='IP address')
    printer_queue_name = models.CharField(max_length=254, null=True, blank=True,
                                          verbose_name='Printer queue name')
    display_address = models.GenericIPAddressField(null=True, blank=True,
                                                   verbose_name='Display IP address')
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    @property
    def printer(self) -> Union[CashdeskPrinter, DummyPrinter]:
        if self.printer_queue_name:
            return CashdeskPrinter(self.printer_queue_name)
        return DummyPrinter()

    @property
    def display(self) -> Union[OverheadDisplay, DummyDisplay]:
        if self.display_address:
            return OverheadDisplay(self.ip_address)
        return DummyDisplay()

    def get_active_sessions(self) -> List:
        return [session for session in self.sessions.filter(end__isnull=True) if session.is_active()]


class CashdeskSession(models.Model):
    cashdesk = models.ForeignKey('Cashdesk', related_name='sessions', on_delete=models.PROTECT)
    user = models.ForeignKey('User', on_delete=models.PROTECT)
    start = models.DateTimeField(default=now,
                                 verbose_name='Start of session',
                                 help_text='Default: time of creation.')
    end = models.DateTimeField(null=True, blank=True,
                               verbose_name='End of session',
                               help_text='Only set if session has ended')
    cash_before = models.DecimalField(max_digits=10, decimal_places=2,
                                      verbose_name='Cash in drawer before session')
    cash_after = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True,
                                     verbose_name='Cash in drawer after session')
    backoffice_user_before = models.ForeignKey('User', on_delete=models.PROTECT,
                                               related_name='supervised_session_starts',
                                               verbose_name='Backoffice operator before session')
    backoffice_user_after = models.ForeignKey('User', on_delete=models.PROTECT,
                                              null=True, blank=True,
                                              related_name='supervised_session_ends',
                                              verbose_name='Backoffice operator after session')
    api_token = models.CharField(max_length=254, default=generate_key,
                                 verbose_name='API token',
                                 help_text='Used for non-browser sessions. Generated automatically.')
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return '#{2} ({0} on {1})'.format(self.user, self.cashdesk, self.pk)

    def is_active(self) -> bool:
        return (not self.start or self.start < now()) and not self.end

    def get_item_set(self) -> List[Item]:
        return [Item.objects.get(pk=pk)
                for pk in self.item_movements.order_by().values_list('item', flat=True).distinct()]

    def get_current_items(self) -> List[Dict]:
        transactions = TransactionPositionItem.objects\
            .values('item')\
            .filter(position__transaction__session=self)\
            .exclude(position__type='reverse')\
            .filter(position__reversed_by=None)\
            .annotate(total=models.Sum('amount'))
        item_movements = self.item_movements\
            .values('item')\
            .annotate(total=models.Sum('amount'))

        post_movement_dict = {}
        if self.end:
            post_movements = item_movements.filter(timestamp__gte=self.end)
            item_movements = item_movements.filter(timestamp__lt=self.end)
            post_movement_dict = {d['item']: {'total': d['total']} for d in post_movements}
        movement_dict = {d['item']: {'total': d['total']} for d in item_movements}
        transaction_dict = {d['item']: {'total': d['total']} for d in transactions}

        DEFAULT = {'total': 0}
        return [
            {
                'item': item,
                'movements': movement_dict.get(item.pk, DEFAULT)['total'],
                'transactions': transaction_dict.get(item.pk, DEFAULT)['total'],
                'final_movements': -post_movement_dict.get(item.pk, DEFAULT)['total'] if self.end else 0,
                'total': movement_dict.get(item.pk, DEFAULT)['total']
                + post_movement_dict.get(item.pk, DEFAULT)['total']
                - transaction_dict.get(item.pk, DEFAULT)['total'],
            }
            for item in self.get_item_set()
        ]

    def get_cash_transaction_total(self) -> Decimal:
        return TransactionPosition.objects\
            .filter(transaction__session=self)\
            .filter(type__in=['sell', 'reverse'])\
            .aggregate(total=models.Sum('value'))['total'] or 0

    def get_product_sales(self) -> List[Dict]:
        qs = TransactionPosition.objects.filter(transaction__session=self)
        result = []

        for p in qs.order_by().values('product').distinct():
            product = Product.objects.get(pk=p['product'])
            product_query = qs.filter(product=product)
            summary = {
                'product': product,
                'sales': product_query.filter(type='sell').count(),
                'presales': product_query.filter(type='redeem').count(),
                'reversals': product_query.filter(type='reverse').count(),
                'value_single': product_query.values_list('value')[0][0],
            }
            summary['value_total'] = (summary['sales'] - summary['reversals']) * summary['value_single']
            result.append(summary)
        return result

    def get_report_path(self) -> Union[str, None]:
        base = default_storage.path('reports')
        search = os.path.join(base, '{}_sessionreport_{}-*.pdf'.format(
            EventSettings.objects.get().short_name,
            self.pk)
        )
        all_reports = sorted(glob.glob(search))

        if all_reports:
            return all_reports[-1]
        return None

    def get_new_report_path(self) -> str:
        return os.path.join(
            'reports',
            '{}_sessionreport_{}-{}.pdf'.format(
                EventSettings.objects.get().short_name,
                self.pk,
                now().strftime('%Y%m%d-%H%M')
            ),
        )

    def request_resupply(self) -> None:
        TroubleshooterNotification.objects.create(
            session=self,
            modified_by=self.user,
            message='Requesting resupply',
        )

    def has_open_requests(self) -> bool:
        return TroubleshooterNotification.objects.active(session=self).exists()


class ItemMovement(models.Model):
    """ Instead of a through-table. Negative amounts indicate items moved out
    of a session, this mostly happens when a session is closed and all remaining
    items are removed and counted manually. """
    session = models.ForeignKey('CashdeskSession', on_delete=models.PROTECT,
                                related_name='item_movements',
                                verbose_name='Session the item was involved in')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             related_name='item_movements',
                             verbose_name='Item moved to/from this session')
    amount = models.IntegerField(help_text='Negative values indicate that items were taken out of a session. '
                                           'Mostly used when counting items after ending a session.')
    backoffice_user = models.ForeignKey('User', on_delete=models.PROTECT,
                                        related_name='supervised_item_movements',
                                        verbose_name='Backoffice operator issuing movement')
    timestamp = models.DateTimeField(default=now, editable=False)


class NotificationsManager(models.Manager):
    def active(self, session=None) -> models.QuerySet:
        qs = self.get_queryset().filter(
            status=TroubleshooterNotification.STATUS_NEW,
            created__gt=now() - timedelta(minutes=10),
            session__end__isnull=True,
        )
        return qs.filter(session=session) if session else qs


class TroubleshooterNotification(models.Model):
    """
    Used for resupply requests at the moment.
    """
    STATUS_ACK = 'ACK'
    STATUS_NEW = 'New'
    STATUS_CHOICES = [
        (STATUS_ACK, STATUS_ACK),
        (STATUS_NEW, STATUS_NEW),
    ]

    session = models.ForeignKey('CashdeskSession', verbose_name='Cashdesk session initiating the notification')
    message = models.CharField(max_length=500)
    created = models.DateTimeField(default=now, editable=False)
    modified = models.DateTimeField(default=now)
    modified_by = models.ForeignKey('User')
    status = models.CharField(choices=STATUS_CHOICES, default=STATUS_NEW, max_length=3)

    objects = NotificationsManager()

    def save(self, *args, **kwargs):
        self.modified = now()
        return super().save(*args, **kwargs)
