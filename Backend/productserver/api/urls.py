from django.urls import path
from .views import *
url_patterns = [
    path("item/<str:pid>",get_item,name="get_item"),
    path("search/",search,name="search"),
    path("home/",home,name="home"),
    path("home_cache/",home_cache,name="home_cache"),
    path('store/',store_data,name="store_data"),
    path('reviews/',get_review,name="get_review"),
    path('summarize/',summarizer,name="summarize"),
    path('chat/',chat,name="chatbot"),
    path('coshop/create/',create_link,name="coshop_link_create"),
    path('coshop/chat/<str:chat_id>/',coshop,name="coshop_chat_page"),
    path('coshop/history/',chat_history,name="chat_history"),
    path('recommend/',recommender,name="recommendation"),
]