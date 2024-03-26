from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    path("llm-test", llmResponse),
    path("llm-engine", chatbot_engine),
]

# my_startup_code()