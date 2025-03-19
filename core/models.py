from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class User(AbstractUser):
    company_name = models.CharField(_('Company Name'), max_length=255, blank=True)
    billing_address = models.TextField(_('Billing Address'), blank=True)
    vat_id = models.CharField(_('VAT ID'), max_length=50, blank=True)
    credits = models.DecimalField(_('Credits'), max_digits=10, decimal_places=2, default=0)
    free_previews_remaining = models.IntegerField(_('Free Previews Remaining'), default=0)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email

class CreditPack(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    credits = models.IntegerField(_('Credits'))
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2)
    free_previews = models.IntegerField(_('Free Previews'))
    preview_credit_cost = models.DecimalField(
        _('Preview Credit Cost'),
        max_digits=3,
        decimal_places=1,
        default=Decimal('0.2')
    )
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Credit Pack')
        verbose_name_plural = _('Credit Packs')
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {self.credits} credits"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('PURCHASE', _('Purchase')),
        ('VECTORIZATION', _('Vectorization')),
        ('PREVIEW', _('Preview')),
    ]

    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(_('Transaction Type'), max_length=20, choices=TRANSACTION_TYPES)
    credit_pack = models.ForeignKey(CreditPack, on_delete=models.SET_NULL, null=True, blank=True)
    credits_amount = models.DecimalField(_('Credits Amount'), max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(_('Amount Paid'), max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    stripe_payment_id = models.CharField(_('Stripe Payment ID'), max_length=100, blank=True)
    invoice_number = models.CharField(_('Invoice Number'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.created_at}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXXX
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_invoice = Transaction.objects.filter(
                invoice_number__startswith=f'INV-{date_str}'
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f'INV-{date_str}-{new_number:04d}'
        
        super().save(*args, **kwargs)

class Vectorization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vectorizations')
    filename = models.CharField(_('Filename'), max_length=255)
    credits_used = models.DecimalField(_('Credits Used'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('PENDING', _('Pending')),
            ('COMPLETED', _('Completed')),
            ('FAILED', _('Failed')),
        ],
        default='PENDING'
    )
    result_url = models.URLField(_('Result URL'), blank=True)

    class Meta:
        verbose_name = _('Vectorization')
        verbose_name_plural = _('Vectorizations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.filename} - {self.created_at}"