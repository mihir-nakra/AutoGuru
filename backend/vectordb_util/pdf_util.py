import fitz  # PyMuPDF
import os
import re


def extract_into_text_docs(file_path, output_folder):
 # Open the PDF using PyMuPDF

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_document = fitz.open(file_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        text = page.get_text('text')
        filename = os.path.join(output_folder, f"{page_number + 1}.txt")

    # Create a text file to store the extracted text
        with open(filename, "w", encoding="utf-8") as text_file:
            text_file.write(_remove_specific_phrases(text))

    # Close the PDF document
    pdf_document.close()

def _remove_page_numbers(text):
    # Define a regular expression pattern to match page numbers
    page_number_pattern = re.compile(r'\b\d+\b')

    # Replace page numbers with an empty string
    cleaned_text = re.sub(page_number_pattern, '', text)

    return cleaned_text

def _remove_specific_phrases(text):
    # Define regular expression patterns to match specific phrases
    phrases_to_remove = ['Main Menu', 'Table of Contents']
    phrase_patterns = [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in phrases_to_remove]

    # Replace specific phrases with an empty string
    for pattern in phrase_patterns:
        text = re.sub(pattern, '', text)

    return text
