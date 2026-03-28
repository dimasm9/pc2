from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('approvals/', views.approvals_queue, name='approvals_queue'),
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/new/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('clients/', views.clients_list, name='clients_list'),
]
