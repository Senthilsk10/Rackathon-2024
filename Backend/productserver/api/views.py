import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import DataEntry
import json

# Assuming you've set these in your Django settings
DATA_API_URL = settings.MONGODB_DATA_API_URL
DATA_API_KEY = settings.MONGODB_DATA_API_KEY
DATA_SOURCE = settings.MONGODB_DATA_SOURCE
DATABASE = "Ecommerce"
COLLECTION = "products"

error_message = {"error": "no matching record found"}
projection = {"_id": 0, "url": 0}
listing_projection = {"title": 1, "price": 1, "images": 1, "_id": 0, "pid": 1}

class MongoDataAPI:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Access-Control-Request-Headers": "*",
            "api-key": DATA_API_KEY,
        }

    def _make_request(self, pipeline,reviews=False):
        url = f"{DATA_API_URL}/action/aggregate"
        COLLECTION = "products" if not reviews else "reviews_collection" 
        body = {
            "dataSource": DATA_SOURCE,
            "database": DATABASE,
            "collection": COLLECTION,
            "pipeline": pipeline
        }
        print(body)
        response = requests.post(url, headers=self.headers, json=body)
        return response.json().get("documents", [])
