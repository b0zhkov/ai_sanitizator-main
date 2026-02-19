# Project Title
AI Sanitizator and Rewriter tool

## Description
Application made for sanitizing and rewriting text.
Currently the application supports only English language.
It allows the users to import files (in pdf, docx, txt and html formats) or paste text directly into the application.
Then the user can choose to either sanitiyze or sanitize and rewrite the imported text.
There is a history tab which allows the user to view what they have sanitized or rewritten.
What they see varies on whether they choose to log in or not.
If they choose to log in, they will see at most their 50 most recent sanitizations/rewrites.
If they choose not to log in they will see the sanitizations/rewrites they have done in the current session.
The sanitization process involves using Regex scripts to identify and remove hidden symbols, normalize the punctuation and spacing, etc.
The rewriting process is a multi-step process.
First the cleaned text is getting analyzed behind the scenes for typical AI/SEO signals which will
most definitely get flagged by AI detectors.
Then a verification of those analysis is done by an AI model to confirm their truthfulness. This is the lenghtiest process but it happens in the background so the loading times can be faster. The end result of it is the AI score of the original text.
Then the process of rewriting begins. The LLM is instructed to utilize the findings and data from the analysis and to go over the text to get to know its topic, tone, theme, etc.
This is done to make sure there are no close similarities between the original text and the rewritten text, which will get the rewritten text flagged by AI detectors.
The end goal of the rewritten text is to utilze both longer and shorter sentences which are made up of words and phrases that are typical for human writing.


## Getting Started

### Dependencies

*   **Python Version**: 3.8 or higher (recommended 3.12)
*   **Operating System**: Linux (primary), Windows, macOS
*   **Key Libraries**:
    *   `FastAPI` & `Uvicorn` (Web interface)
    *   `LangChain` (LLM orchestration)
    *   `Spacy` (NLP analysis)
    *   `SQLAlchemy` (ORM for SQLite database)

### Installing

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd ai_sanitizator-main
    ```

2.  **Set up a Virtual Environment**
    Recommended to isolate dependencies.
    ```bash
    # Create venv
    python3 -m venv .venv
    
    # Activate venv
    # Linux/Mac:
    source .venv/bin/activate
    # Windows:
    # .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download NLP Model**
    The app attempts to download the Spacy model automatically, but you can do it manually if needed:
    ```bash
    python -m spacy download en_core_web_sm
    ```

5.  **Configuration**
    Create a `.env` file in the project root with your API keys:
    ```env
    OPENAI_API_KEY=your_key_here
    DATABASE_URL=sqlite:///./sql_app.db
    ```

### Executing program

1.  **Start the Server**
    ```bash
    uvicorn web_app.main:app --reload
    ```

2.  **Access the App**
    Open `http://127.0.0.1:8000` in your browser.

## Help

**Common Issues:**

*   **Missing API Key**: Ensure `.env` exists and contains `OPENAI_API_KEY`.
*   **Model Load Error**: Run `python -m spacy download en_core_web_sm`.
*   **Port In Use**: Use `uvicorn web_app.main:app --reload --port 8080` to try a different port.