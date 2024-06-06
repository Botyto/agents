from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _


class Command(models.Model):
    class CommandStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        EXECUTED = "EXECUTED", _("Executed")
        REVERTED = "REVERTED", _("Reverted")

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, choices=CommandStatus.choices, default=CommandStatus.PENDING)
    tag = models.CharField(max_length=255)
    previous_command = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    command = models.CharField(max_length=255)
    target_app = models.CharField(max_length=255)
    target_model = models.CharField(max_length=255)
    target_pk = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
