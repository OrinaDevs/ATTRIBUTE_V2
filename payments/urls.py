from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/download/', views.download_invoice_pdf, name='download_invoice'),
    path('<int:pk>/pay/', views.mark_payment, name='mark_payment'),
]
