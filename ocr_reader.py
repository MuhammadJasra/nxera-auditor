import fitz  # PyMuPDF
import pytesseract
from PIL import Image

def extract_text_from_pdf(file) -> str:
    data = file.read()
    doc = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)  # type: ignore[attr-defined]

def extract_text_from_image(file) -> str:
    image = Image.open(file)
    return pytesseract.image_to_string(image)
