from abc import ABC, abstractmethod
from typing import ClassVar, Type
from uuid import UUID

from django.db import models

from .models import Command


class AbstractCommand(ABC):
    name: ClassVar[str]
    target_model: ClassVar[Type[models.Model]]
    target_pk: UUID
    payload: dict

    @property
    def target_object(self):
        return self.target_model.objects.get(pk=self.target_pk)

    def __init__(self, target_pk: UUID, payload: dict):
        self.target_pk = target_pk
        self.payload = payload

    def save(self, tag: str, previous_command: Command | None = None):
        return Command.objects.create(
            tag=tag,
            command=self.name,
            previous_command=previous_command,
            target_app=self.target_model._meta.app_label,
            target_model=self.target_model.__name__,
            target_pk=self.target_pk,
            payload=self.payload,
        )

    @abstractmethod
    def execute(self): ...

    @abstractmethod
    def revert(self): ...
