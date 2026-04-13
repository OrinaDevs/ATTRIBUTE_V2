from django.urls import path
from . import views

urlpatterns = [
    path('', views.quotation_list, name='quotation_list'),
    path('request/', views.request_quotation, name='request_quotation'),
    path('request/<slug:slug>/', views.request_quotation, name='request_quotation_for_service'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/respond/', views.quotation_respond, name='quotation_respond'),
]
