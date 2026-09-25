from django.urls import path
from . import views
from .views import download_search_pdf
from .views import download_ai_study_pdf


urlpatterns = [
    path("upload/", views.upload_pdf, name="upload_pdf"),
    path("list/", views.pdf_list, name="pdf_list"),
    path("delete/<int:pdf_id>/", views.delete_pdf, name="delete_pdf"),
    path("search/download/", download_search_pdf, name="download_search_pdf"),
    path("search/study/download/", download_ai_study_pdf, name="download_ai_study_pdf"),
]
