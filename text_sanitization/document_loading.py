"""
The document loading module handles the importing for various file formats.

I have combined the importing logic into a single file to make it easier to maintain and follow DRY.

It achieves this by:
1. Mapping file extensions to specific loader functions (.txt, .docx, .html, .pdf).
2. utilizing specialized libraries like BeautifulSoup, docx2txt, and pypdf to extract text.
3. implementing error handling for unsupported formats and loading failures.

The end goal is to abstract away the file reading complexity and return a clean string.
"""
import os
from bs4 import BeautifulSoup
import docx2txt
from pypdf import PdfReader

def _load_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def _load_docx(file_path: str) -> str:
    return docx2txt.process(file_path)


def _load_html(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        return soup.get_text(separator='\n', strip=True)

def html_specific_content(html_input: str) -> list[dict]:
    soup = BeautifulSoup(html_input, "html.parser")
    
    structured_data = []
    
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        element_type = "heading" if tag.name.startswith('h') else "body"
        
        structured_data.append({
            "type": element_type,
            "tag": tag.name,
            "content": tag.get_text().strip()
        })
        
    return structured_data

def _load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or '' for page in reader.pages]
    return '\n'.join(pages)


_LOADERS = {
    '.txt': _load_txt,
    '.docx': _load_docx,
    '.html': _load_html,
    '.pdf': _load_pdf,
}


def load_file_content(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    loader_fn = _LOADERS.get(ext)
    if not loader_fn:
        supported = ', '.join(_LOADERS.keys())
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: {supported}")

    try:
        return loader_fn(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load file '{file_path}': {e}") from e