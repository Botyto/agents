from django.db import models


class Model(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100)
    base_url = models.CharField(max_length=100)
    max_tokens = models.IntegerField()
    input_price_1k = models.FloatField()
    output_price_1k = models.FloatField()


class Agent(models.Model):
    name = models.CharField(max_length=100)
    model = models.ForeignKey(Model, on_delete=models.SET_DEFAULT, default=None)
    path = models.CharField(max_length=100)
    description_override = models.CharField(max_length=1000)
    prompt_override = models.CharField(max_length=1000)
    init_kwargs = models.JSONField()


class Session(models.Model):
    name = models.CharField(max_length=100)
    agents = models.ManyToManyField(Agent)
    group_chat = models.BooleanField()


class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    content = models.TextField()


class MessageFile(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
