<div align="center">
  <h1>AI Sanitizator & Rewriter</h1>
  <p>A tool made for sanitizing text from hidden symbols and AI fingerprints and rewriting it to achieve a more human-like tone.</p>
</div>

<br />

## 📖 Overview
The **AI Sanitizator and Rewriter** is a web/desktop application which was designed as a tool to help users turn their AI generated text into something that is more human-like.
This process includes importing text from files, images or just writing it in the text box.
Then the text goes through a well constructed pipeline of sanitization, analysis and rewriting.
With a few seconds of waiting the text is ready to be downloaded or copied.

## ✨ Key Features
- **Versatile Input Support:** The user can import text from different file types (ex. 'html', 'pdf', 'txt', etc), images or just write it in the intened text box.
- **Deep Text Sanitization:** The sanitization process includes the removal of hidden symbols, irregular spacing, zero-width characters, html tags, typical markdown symbols, profanties, emojis, etc.
- **AI Analysis & Scoring:** The analysis process is taking place behind the scenes. It judges the original text inputed by the user for the typical AI/SEO signals which are used to identify AI generated text. These being readability score, uniform sentence length, verb frequency, hedging, excessive usage of filler words, etc.
- **Intelligent Rewriting:** Based on the analysis and a well-constructed prompt, the sanitized text is rewritten to fully remove any AI fingerprints and make it a lot more believable, interesting and human-like.
- **User History & Authentication:** There is also the option to log in or stay as a guest. Logged-in users can view their 50 most recent santized/rewritten texts, while the guest users can only see the text which they have sanitized/rewritten in their current session.

## 🛠️ Technology Stack
- **Backend Framework:** FastAPI, Uvicorn
- **AI & NLP Orchestration:** LangChain, Cloudflare API, spaCy
- **Database:** SQLite with SQLAlchemy ORM
- **Document Processing:** PyMuPDF, docx2txt, BeautifulSoup4
- **OCR Integration:** Google Cloud Vision

## 🚀 Getting Started

### Prerequisites
*   **Python Version**: 3.12 is recommended, 3.14 can be unstable due to some dependencies
*   **Operating System**: Linux (primary), Windows, macOS

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai_sanitizator-main
   ```

2. **Set up a Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLP Model**
   The app attempts to download the spaCy model automatically, but you can install it manually:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configuration**
   Create a `.env` file in the project root with your credentials:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   DATABASE_URL=sqlite:///./sanitizator.db
   ```

### Running the Application

1. **Start the Development Server**
   ```bash
   uvicorn web_app.main:app --reload
   ```

2. **Access the Web Interface**
   Open your browser and navigate to: `http://127.0.0.1:8000`

## ❓ Troubleshooting

*   **Missing API Key:** Ensure your `.env` file exists and contains a valid `OPENAI_API_KEY`.
*   **Model Load Error:** Run `python -m spacy download en_core_web_sm` to install the required English NLP model.
*   **Port in Use:** If port 8000 is taken, start the server on a different port:
    ```bash
    uvicorn web_app.main:app --reload --port 8080
    ```
*   **ModuleNotFoundError for OCR/Deployment:** Ensure all dependencies from `requirements.txt` are installed, particularly when deploying to platforms like Vercel.