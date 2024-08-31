import requests
from django.conf import settings
from django.http import JsonResponse
from .gemini import *
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import DataEntry,CoShop,UserBehavior
import json
import markdown
from datetime import datetime
from bson import ObjectId 


# Assuming you've set these in your Django settings
DATA_API_URL = settings.MONGODB_DATA_API_URL
DATA_API_KEY = settings.MONGODB_DATA_API_KEY
DATA_SOURCE = settings.MONGODB_DATA_SOURCE
DATABASE = "Ecommerce"
COLLECTION = "products"

error_message = {"error": "no matching record found"}
projection = {"_id": 0, "url": 0}
summary_projection = {"_id": 0, "url": 0,"title":0,"images":0,"brand":1}
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
        
    def _make_request_coshop(self, endpoint, body):
        url = f"{DATA_API_URL}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=body)
        return response.json()

    def create_document(self, data,html="<h2>CoSHop</h2>"):
        data['chat'] = [{"bot":f"Hey! {data['user']} shared a products with you.\n take a look","msg":html}]
        body = {
            "dataSource": DATA_SOURCE,
            "database": DATABASE,
            "collection": "coshop",
            "document": data
        }
        response = self._make_request_coshop("action/insertOne", body)
        inserted_id = response.get("insertedId", None)
        return inserted_id

    def push_chat(self, document_id, msg):
        new_value = {
            "msg": msg,
            "timestamp": datetime.utcnow().isoformat()
        }

        update_body = {
            "dataSource": DATA_SOURCE,
            "database": DATABASE,
            "collection": "coshop",
            "filter": {"_id": {"$oid":document_id}},
            "update": {
                "$push": {"chat": new_value}
            }
        }

        update_response = self._make_request_coshop("action/updateOne", update_body)
        
        return "updated"

    
    def get_item_by_oid(self, oid):
        print(oid)
        pipeline = [
            {"$match": {"_id": {"$oid": oid}}}
        ]
        
        body = {
            "dataSource": DATA_SOURCE,
            "database": DATABASE,
            "collection": "coshop",
            "pipeline": pipeline
        }
        print(body)
        response = None
        try:
            response = self._make_request_coshop("action/aggregate", body)
            print(response)
        
            result = response.get("documents", [])
            return result[0] if result else {"error": "Document not found"}
        except:
            return response
    def make_request(self, pipeline,reviews=False):
        url = f"{DATA_API_URL}/action/aggregate"
        COLLECTION = "products" if not reviews else "reviews_collection" 
        body = {
            "dataSource": DATA_SOURCE,
            "database": DATABASE,
            "collection": COLLECTION,
            "pipeline": pipeline
        }
        
        response = requests.post(url, headers=self.headers, json=body)
        # print("first " ,response.json())
        return response.json().get("documents", [])

    def get_item(self, pid):
        pipeline = [
            {"$match": {"pid": pid}},
            {"$project": projection},
            {"$limit": 1}
        ]
        result = self.make_request(pipeline)
        return result[0] if result else error_message
    
    
    def get_item_invoked(self, pid):
        pipeline = [
            {"$match": {"pid": {"$in":pid}}},
            {"$project": summary_projection}
        ]
        # print(pipeline)
        result = self.make_request(pipeline)
        # print(result)
        return result[0] if result else error_message

    def get_category_data(self, category, samples):
        pipeline = [
            {"$match": {"sub_category": category, "$expr": {"$gt": [{"$size": "$images"}, 1]}}},
            {"$sample": {"size": int(samples)}},
            {"$project": listing_projection}
        ]
        return self.make_request(pipeline)

    def get_categories(self):
        pipeline = [
            {"$group": {"_id": "$sub_category"}},
            {"$project": {"_id": 0, "category": "$_id"}},
            {"$sort": {"category": 1}}
        ]
        result = self.make_request(pipeline)
        return [doc["category"] for doc in result]

    def search(self, query, limit=10, skip=0,ai=False):
        global listing_projection
        if ai:
            listing_projection = {
                "title": 1,
                "price": 1,
                "pid": 1,
                "product_details": 1,
                "_id": 0
            }

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
        result = self.make_request(pipeline)
        # print(result)
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

        result = self.make_request(pipeline,reviews=True)
        return result[0] if result else {"results": []}


def recommend_prompt(prompt, selected, prev=None):
    mongo = MongoDataAPI()
    global model
    
    # Retrieve product details
    products = mongo.search(selected['product']['title'], limit=10,ai=True)
    
    # Ensure products are formatted as a string
    products_str = json.dumps(products, indent=2)  # Convert products to a pretty-printed JSON string
    
    # Construct the base prompt
    base_prompt = (
        "You are a shopping assistant for an e-commerce site where you are given a dictionary of product details. "
        "You have to analyze and answer queries from the user based on the product details."
        "Provide a response as pid for selected products from the products use pid:<selected pid> format."
        f"here is your Prompt you have to answer: {prompt}\nProduct details for providing answers: {str(products)} where the already selected product was {selected['product']}."
        " Please provide a valid response while inferring by assisting user to choose th best from products. and dont leave empty text fields in response"
    )
    
    prev_history = f"Here is the previous chat history:\n{prev}\n" if prev else ""
    
    prompt_text = base_prompt + prev_history
    print("prompt : \n",prompt_text)
    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        resp = response.to_dict()
        # data = json.loads(response.to_dict())
        print(resp)
        pid = (json.loads(resp["candidates"][0]["content"]["parts"][0]["text"])["pid"])
        # text_part = data["candidates"][0]["content"]["parts"][0]["text"]
        return pid
    except Exception as e:
        print(f"Error parsing initial response: {e}")
        resp = None
    return resp

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

@csrf_exempt
def create_link(request):
    if request.method == "POST":
        body = json.loads(request.body)
        user = body.get("user",None)
        product = body.get("product")
        friend = body.get("friend",None)
        if user is None or friend is None:
            return cors_response(JsonResponse({"error":"both user's and friend's id is required"}))
        mongo = MongoDataAPI()
        id = mongo.create_document({"user":user,"friend":friend,"product":product})
        
        CoShop.objects.create(user=user,url_id=id)
        
        return cors_response(JsonResponse({"url_id":id},status=200,safe=False))
        
        
@csrf_exempt
def coshop(request,*args,**kwargs):
    doc_id = kwargs.get("chat_id")
    mongo  = MongoDataAPI()
    if request.method == "POST":
        body = json.loads(request.body)
        selected = mongo.get_item_by_oid(doc_id)
        # print("from coshop",selected)
        # print("from coshop",selected['product']['title'])
        messenger = body.get("messenger")
        if messenger == selected['user']:
            messenger = 'user'
        else:
            messenger = 'friend'
        if messenger == "user":
            msg = body.get("msg")
            
            chat = mongo.push_chat(doc_id,{"from":"user","msg":msg})
            
            if "/AI" in msg:
                response = recommend_prompt(msg,selected)
                chat = mongo.push_chat(doc_id,{"from":"bot","msg":response})
                
            return cors_response(JsonResponse(chat,safe=False,status=200))
        elif messenger == "friend":
            msg = body.get("msg")
            chat = mongo.push_chat(doc_id,{"from":"friend","msg":msg})
            return cors_response(JsonResponse(chat,safe=False,status=200))
        
        else:
            return cors_response(JsonResponse({"error":"no outsiders are allowed to message"},safe=False,status=200))



@csrf_exempt
def chat_history(request):
    if request.method == "POST":
        body = json.loads(request.body)
        oid = body.get("oid")
        print(oid)
        mongo = MongoDataAPI()
        data = mongo.get_item_by_oid(oid)
        
        return data['chat']
    
    
    
@csrf_exempt
def recommender(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        id = body.get('user_id')
        behavior = UserBehavior.objects.get(user_id=id)
        prodcuts = body.get('products')
        print(behavior.data)
        recommendations = gemini_recommender(behavior,prodcuts)
        
        return cors_response(JsonResponse(recommendations),safe=False,status=200)
    