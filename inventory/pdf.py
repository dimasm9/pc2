from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML


def render_document_pdf(template_name: str, context: dict, filename: str) -> str:
    html = render_to_string(template_name, context)
    output_dir = Path(settings.MEDIA_ROOT) / 'documents'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    HTML(string=html).write_pdf(output_path)
    return str(output_path.relative_to(settings.MEDIA_ROOT))
