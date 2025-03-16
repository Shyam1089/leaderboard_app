import random
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    address = models.TextField()
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Winner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="winners")
    points_at_win = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.points_at_win} points at {self.timestamp}"
