import pdfplumber
# from pypdf2 import PdfReader
import os
import docx

# Extracting text from pdfs using pdfplumber
def pdf_extraction(file_path):
  with pdfplumber.open(file_path,encoding="utf-8") as resume_pdf:
    text_in_resume=""
    for p in resume_pdf.pages:
      text_in_resume=" ".join([text_in_resume,p.extract_text()])
  text_in_resume=text_in_resume.strip()
  return text_in_resume

def extract_text_from_docx(docx_path):
  doc = docx.Document(docx_path)
  text = "\n".join([para.text for para in doc.paragraphs])
  return text