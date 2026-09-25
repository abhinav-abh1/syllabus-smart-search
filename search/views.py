from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pdf_manager.models import UploadedPDF
from .relevance import find_relevant_content
import logging

logger = logging.getLogger(__name__)


@login_required
def topic_search(request):
    pdfs = UploadedPDF.objects.filter(user=request.user)

    query = ""
    selected_pdf = None
    result = None
    error_message = None

    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        pdf_id = request.POST.get("pdf")

        if not query:
            error_message = "Please enter a topic name."
        elif not pdf_id:
            error_message = "Please select a textbook."
        else:
            try:
                selected_pdf = int(pdf_id)
                pdf = UploadedPDF.objects.get(id=selected_pdf, user=request.user)

                result = find_relevant_content(pdf, query)

                if result is None:
                    error_message = (
                        "No reliable textbook definition was found for this topic. "
                        "Try a more specific wording or check if the correct PDF is selected."
                    )

            except UploadedPDF.DoesNotExist:
                error_message = "Selected textbook not found."
            except ValueError:
                error_message = "Invalid textbook selection."
            except Exception as e:
                logger.error(f"Unexpected error during search: {e}")
                error_message = "An unexpected error occurred. Please try again."

    return render(
        request,
        "search/result.html",
        {
            "pdfs": pdfs,
            "query": query,
            "selected_pdf": selected_pdf,
            "result": result,
            "error_message": error_message,
        },
    )