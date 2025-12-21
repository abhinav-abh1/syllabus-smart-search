from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def home(request):
    if request.user.is_authenticated:
        return redirect("upload_pdf")
    return redirect("login")


urlpatterns = [
    path("admin/", admin.site.urls),
    # 👇 Root URL
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("pdf/", include("pdf_manager.urls")),
    path("search/", include("search.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
