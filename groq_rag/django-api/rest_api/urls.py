# In your Django app's urls.py
from django.urls import path
from .views import process_query_view

urlpatterns = [
    path('process-query/', process_query_view, name='process_query'),
]
