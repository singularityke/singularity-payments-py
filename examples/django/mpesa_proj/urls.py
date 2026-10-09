from django.urls import include, path

urlpatterns = [
    path("", include("mpesa_app.urls")),
]