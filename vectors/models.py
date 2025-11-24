from django.db import models
from pgvector.django import VectorField

# Create your models here.


class Item(models.Model):
    embedding = VectorField(dimensions=768)
