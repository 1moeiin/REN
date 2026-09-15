from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("services/", views.service_list, name="service_list"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
