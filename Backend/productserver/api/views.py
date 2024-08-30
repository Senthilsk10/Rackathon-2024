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

    def get_item(self, pid):
        pipeline = [
            {"$match": {"pid": pid}},
            {"$project": projection},
            {"$limit": 1}
        ]
        result = self._make_request(pipeline)
        return result[0] if result else error_message

    def get_category_data(self, category, samples):
        pipeline = [
            {"$match": {"sub_category": category, "$expr": {"$gt": [{"$size": "$images"}, 1]}}},
            {"$sample": {"size": int(samples)}},
            {"$project": listing_projection}
        ]
        return self._make_request(pipeline)

    def get_categories(self):
        pipeline = [
            {"$group": {"_id": "$sub_category"}},
            {"$project": {"_id": 0, "category": "$_id"}},
            {"$sort": {"category": 1}}
        ]
        result = self._make_request(pipeline)
        return [doc["category"] for doc in result]

    def search(self, query, limit=10, skip=0):
        pipeline = [
            {"$match": {
                "$text": {"$search": query},
                "$expr": {"$gt": [{"$size": "$images"}, 1]}
            }},
            {"$project": listing_projection},
            {"$skip": skip},
            {"$limit": limit},
            {"$facet": {
                "results": [],
                "totalCount": [{"$count": "count"}]
            }},
            {"$project": {
                "results": 1,
                "paging": {
                    "limit": {"$literal": limit},
                    "skip": {"$literal": skip},
                    "count": {"$arrayElemAt": ["$totalCount.count", 0]}
                }
            }}
        ]
        result = self._make_request(pipeline)
        return result[0] if result else {"results": [], "paging": {"limit": limit, "skip": skip, "count": 0}}
    def get_review(self, category):
        pipeline = pipeline = [
            {
                "$match": {
                    "category": "Blazers, Waistcoats and Suits"
                }
            },
            {
                "$sample": {
                    "size": 10
                }
            },
            {
                "$group": {
                    "_id": None,
                    "documents": { "$push": "$$ROOT" },
                    "ratings": { "$push": "$rating" }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "documents": 1,
                    "ratings": 1
                }
            } 
        ]

        result = self._make_request(pipeline,reviews=True)
        return result[0] if result else {"results": []}
    
    
    
    
def home_cache(request):
    data = None
    with open("cache.json","r") as f:
        data = json.loads(f.read())
    response = JsonResponse(data, safe=False, status=200)
    response["Access-Control-Allow-Origin"] = "*"
    return response


def get_review(request):
    category= request.GET.get("category")
    mongo = MongoDataAPI()
    results = mongo.get_review(category)
    response = JsonResponse(results, safe=False, status=200)
    response["Access-Control-Allow-Origin"] = "*"
    return response
    