from django.contrib import admin
from . import models

admin.site.register(models.Model)
admin.site.register(models.Agent)
admin.site.register(models.Session)
admin.site.register(models.Message)
admin.site.register(models.MessageFile)
