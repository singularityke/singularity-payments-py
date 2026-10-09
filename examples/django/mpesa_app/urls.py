from django.urls import path

from . import views

urlpatterns = [
    path("api/mpesa/stk-push", views.stk_push),
    path("api/mpesa/callback", views.stk_callback),
]