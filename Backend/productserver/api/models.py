
from django.db import models

class DataEntry(models.Model):
    user_id = models.IntegerField()
    json_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DataEntry for user {self.user_id} at {self.timestamp}"
