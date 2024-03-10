from django.contrib import admin
from django.urls import path
from .views import *
from .startup import my_startup_code

urlpatterns = [
    path("admin/", admin.site.urls),
    path("llm-test", llmResponse),
    path("llm", getResponse),
]

# my_startup_code()