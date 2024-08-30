import requests
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from .gemini import update_behavior

class UserBehavior(models.Model):
    user_id = models.IntegerField()
    data = models.JSONField()
    
    def __str__(self):
        return f"behavior of {self.user_id}"
    
    
class DataEntry(models.Model):
    user_id = models.IntegerField()
    json_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        obj = None
        
        try:
            obj = UserBehavior.objects.get(user_id=self.user_id)
        except UserBehavior.DoesNotExist:
            obj = UserBehavior.objects.create(user_id=self.user_id,data=update_behavior(self.json_data))
        except Exception as e:
            print("exception in models.py confirmed")
        
        try:
            data = update_behavior(self.json_data,obj.data)
            print(data['message'])
            obj.data = update_behavior(self.json_data,data['message'])
            obj.save()
            super().save(*args, **kwargs)
        except:
            print("exception at models.py")

    def __str__(self):
        return f"DataEntry for user {self.user_id} at {self.timestamp}"
