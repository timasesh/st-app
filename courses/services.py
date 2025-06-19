import os
from django.conf import settings
from PIL import Image
import fitz  # PyMuPDF for PDF processing
from pptx import Presentation

# Ensure MEDIA_ROOT/slides exists
SLIDES_ROOT = os.path.join(settings.MEDIA_ROOT, 'slides')
os.makedirs(SLIDES_ROOT, exist_ok=True)

def convert_pdf_to_images(pdf_path, lesson_id):
    """
    Converts each page of a PDF into an image and saves it.
    Requires PyMuPDF (fitz) and Pillow.
    """
    images_paths = []
    try:
        doc = fitz.open(pdf_path)
        output_dir = os.path.join(SLIDES_ROOT, str(lesson_id))
        os.makedirs(output_dir, exist_ok=True)

        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img_path = os.path.join(output_dir, f'page_{i+1}.png')
            pix.save(img_path)
            images_paths.append(img_path)
        doc.close()
    except Exception as e:
        print(f"Error converting PDF {pdf_path}: {e}")
        # Log the error, maybe send a notification to admin
    return images_paths

def convert_pptx_to_images(pptx_path, lesson_id):
    """
    Converts each slide of a PPTX into an image and saves it.
    Requires python-pptx and Pillow.
    """
    images_paths = []
    try:
        prs = Presentation(pptx_path)
        output_dir = os.path.join(SLIDES_ROOT, str(lesson_id))
        os.makedirs(output_dir, exist_ok=True)

        for i, slide in enumerate(prs.slides):
            # python-pptx does not directly render slides to images.
            # This is a placeholder. A more robust solution would involve
            # using an external tool like LibreOffice/PowerPoint automation
            # or a cloud service.
            # For simplicity, we'll just create a dummy image for now or skip.
            # This part needs significant external tool integration.
            # For this example, we'll assume a dummy image or error.
            print(f"Warning: Direct PPTX to image conversion not fully supported without external tools. Skipping slide {i+1} of {pptx_path}")
            # As a workaround for demonstration, let's create a blank image if no external tool is set up.
            dummy_img = Image.new('RGB', (1024, 768), color = (255, 255, 255))
            img_path = os.path.join(output_dir, f'slide_{i+1}.png')
            dummy_img.save(img_path)
            images_paths.append(img_path)
            
    except Exception as e:
        print(f"Error converting PPTX {pptx_path}: {e}")
    return images_paths

def handle_lesson_file_conversion(lesson_instance):
    """
    Handles the conversion of PDF/PPTX files associated with a lesson
    into a series of images if convert_pdf_to_slides is True.
    """
    if lesson_instance.convert_pdf_to_slides and lesson_instance.pdf:
        file_extension = os.path.splitext(lesson_instance.pdf.path)[1].lower()
        if file_extension == '.pdf':
            print(f"Converting PDF: {lesson_instance.pdf.path}")
            return convert_pdf_to_images(lesson_instance.pdf.path, lesson_instance.id)
        elif file_extension in ['.pptx', '.ppt']:
            print(f"Converting PPTX: {lesson_instance.pdf.path}")
            return convert_pptx_to_images(lesson_instance.pdf.path, lesson_instance.id)
    return [] 