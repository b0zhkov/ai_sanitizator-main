import os


def _load_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def _load_docx(file_path: str) -> str:
    import docx2txt
    return docx2txt.process(file_path)


def _load_html(file_path: str) -> str:
    from bs4 import BeautifulSoup
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        return soup.get_text(separator='\n', strip=True)


def _load_pdf(file_path: str) -> str:
    from pypdf import PdfReader
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