import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import DataEntry
import json
from .gemini import *
import markdown

# Assuming you've set these in your Django settings
DATA_API_URL = settings.MONGODB_DATA_API_URL
DATA_API_KEY = settings.MONGODB_DATA_API_KEY
DATA_SOURCE = settings.MONGODB_DATA_SOURCE
DATABASE = "Ecommerce"
COLLECTION = "products"

error_message = {"error": "no matching record found"}
projection = {"_id": 0, "url": 0}
summary_projection = {"_id": 0, "url": 0,"title":0,"images":0}
listing_projection = {"title": 1, "price": 1, "images": 1, "_id": 0, "pid": 1}


def cors_response(response):
    response["Access-Control-Allow-Origin"] = '*'
    return response

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
    def get_item_invoked(self, pid):
        pipeline = [
            {"$match": {"pid": {"$in":pid}}},
            {"$project": summary_projection}
        ]
        print(pipeline)
        result = self._make_request(pipeline)
        print(result)
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
@csrf_exempt
def home(request):
    samples = int(request.GET.get("samples", 7))
    mongo = MongoDataAPI()
    categories = mongo.get_categories()
    data = {}
    for category in categories:
        products = mongo.get_category_data(category, samples=samples)
        data[category] = products
    
    return cors_response(JsonResponse(data, safe=False, status=200))
    
@csrf_exempt
def get_item(request, **kwargs):
    pid = kwargs.get("pid", None)
    mongo = MongoDataAPI()
    item = mongo.get_item(pid)
    return cors_response(JsonResponse(item, safe=False, status=200))
    
@csrf_exempt
def search(request):
    query = request.GET.get("query")
    limit = int(request.GET.get("limit", 10))
    skip = int(request.GET.get("skip", 0))
    mongo = MongoDataAPI()
    results = mongo.search(query, limit, skip)
    return cors_response(JsonResponse(results,status=200,safe=False))

@csrf_exempt
def store_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            json_data = data.get('json_data')

            if not user_id or not json_data:
                return cors_response(JsonResponse({'error': 'Invalid data provided'}, status=400))
                
            DataEntry.objects.create(user_id=user_id, json_data=json_data)

            return cors_response(JsonResponse({'status': 'success', 'message': 'Data stored successfully'}, status=201))
           
        except json.JSONDecodeError:
            return cors_response(JsonResponse({'error': 'Invalid JSON'}, status=400))
            
        except Exception as e:
            return cors_response(JsonResponse({'error': str(e)}, status=500))
            
    else:
        return cors_response(JsonResponse({'error': 'Invalid request method'}, status=405))
        
    

def home_cache(request):
    data = None
    with open("cache.json","r") as f:
        data = json.loads(f.read())
    return cors_response(JsonResponse(data,safe=False,status = 200))

def get_review(request):
    category= request.GET.get("category")
    mongo = MongoDataAPI()
    results = mongo.get_review(category)
    return cors_response(JsonResponse(results, safe=False, status=200))
    
    
    
@csrf_exempt
def summarizer(request):
    if request.method == "POST":
        print(request.POST)
        pids = json.loads(request.body)["pids"]
        mongo = MongoDataAPI()
        products = mongo.get_item_invoked(pids)
        print(products)
        response = summarize(products)
        # html = markdown.markdown(response.get('message',"### Error fetching summary"))
        html = (response.get('message',"### Error fetching summary"))
        return  cors_response(JsonResponse({"html":html},safe=False,status=200))
        
    
    
    
@csrf_exempt
def chat(request):
    data= json.loads(request.body)
    query,prod,history = data['query'],data['product'],data.get("history",None)
    response = chat_completion({"query":query,"products":prod},prev=history)
    
    
    html = markdown.markdown(response.get("message","### error contacting chatbot"))
    return  cors_response(JsonResponse({"html":html},safe=False,status=200))