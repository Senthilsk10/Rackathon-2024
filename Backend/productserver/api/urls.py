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
]