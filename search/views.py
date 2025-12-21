from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pdf_manager.models import UploadedPDF
from .relevance import find_relevant_content


@login_required
def topic_search(request):
    pdfs = UploadedPDF.objects.filter(user=request.user)

    query = ""
    selected_pdf = None
    result = None

    if request.method == "POST":
        query = request.POST.get("query")
        selected_pdf = int(request.POST.get("pdf"))

        if query and selected_pdf:
            pdf = UploadedPDF.objects.get(id=selected_pdf, user=request.user)

            # ✅ SINGLE result object
            result = find_relevant_content(pdf, query)

    return render(
        request,
        "search/result.html",
        {
            "pdfs": pdfs,
            "query": query,
            "selected_pdf": selected_pdf,
            "result": result,
        },
    )
