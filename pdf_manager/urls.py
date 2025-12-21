from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_pdf, name="upload_pdf"),
    path("list/", views.pdf_list, name="pdf_list"),
    path("delete/<int:pdf_id>/", views.delete_pdf, name="delete_pdf"),
]
