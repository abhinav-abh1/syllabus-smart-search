from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import UploadedPDF
from .pdf_utils import extract_pdf_content
from .embedding_utils import store_text_embeddings
from django.shortcuts import get_object_or_404

from django.http import HttpResponse
from .utils.pdf_export import generate_search_result_pdf
from .models import ExtractedText, ExtractedDiagram
from search.ai_study_material import generate_study_material
from .utils.study_pdf_export import generate_study_material_pdf


@login_required
def upload_pdf(request):
    """
    Handles PDF upload, extraction, and semantic indexing
    """
    if request.method == "POST":
        title = request.POST.get("title")
        pdf_file = request.FILES.get("pdf_file")

        # Validation
        if not title or not pdf_file:
            messages.error(request, "Please provide both title and PDF file.")
            return redirect("upload_pdf")

        uploaded_pdf = UploadedPDF.objects.create(
            user=request.user, title=title, pdf_file=pdf_file
        )

        extract_pdf_content(uploaded_pdf)
        store_text_embeddings(uploaded_pdf)

        messages.success(request, "PDF uploaded, processed, and indexed successfully.")
        return redirect("pdf_list")

    # GET request
    return render(request, "pdf/upload.html")


@login_required
def pdf_list(request):
    """
    Displays list of uploaded PDFs (user-specific)
    """
    pdfs = UploadedPDF.objects.filter(user=request.user).order_by("-uploaded_at")
    return render(request, "pdf/pdf_list.html", {"pdfs": pdfs})


@login_required
def delete_pdf(request, pdf_id):
    pdf = get_object_or_404(
        UploadedPDF, id=pdf_id, user=request.user  # 🔐 security check
    )

    if request.method == "POST":
        pdf.pdf_file.delete(save=False)  # delete file
        pdf.delete()  # delete DB record
        messages.success(request, "PDF deleted successfully.")
        return redirect("pdf_list")

    return redirect("pdf_list")


def download_search_pdf(request):
    topic = request.GET.get("topic")

    if not topic:
        return HttpResponse("Topic missing", status=400)

    explanation = request.session.get("ai_explanation", "")
    contents = ExtractedText.objects.filter(content__icontains=topic).order_by(
        "page_number"
    )[:20]

    pdf_buffer = generate_search_result_pdf(
        topic=topic,
        explanation=explanation,
        contents=contents,
    )

    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{topic}.pdf"'
    return response


def download_ai_study_pdf(request):
    topic = request.GET.get("topic")
    if not topic:
        return HttpResponse("Topic missing", status=400)

    # Fetch relevant text
    contents = ExtractedText.objects.filter(content__icontains=topic).order_by(
        "page_number"
    )[:5]

    # Fetch relevant diagrams (same pages)
    pages = {c.page_number for c in contents}
    diagrams = ExtractedDiagram.objects.filter(page_number__in=pages)[:3]

    # Generate grounded AI study notes
    study_text = generate_study_material(topic, contents)

    # Generate PDF WITH images
    pdf_buffer = generate_study_material_pdf(
        topic=topic, study_text=study_text, diagrams=diagrams
    )

    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{topic}_AI_Study_Material.pdf"'
    )
    return response
