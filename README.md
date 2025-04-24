# Privacy Policy Explorer

This project is a Streamlit-powered app that helps researchers explore and analyze privacy policies. It supports question-answering, summarization, and chunk-based citation highlighting from long-form policy text using OpenAI and LangChain.

---

## Features

-   Select a company and view its most recent `.txt` privacy policy
-   Ask natural language questions like:
    -   “Where do they mention data sharing?”
    -   “What are the most surprising uses of data?”
-   Generate 3–5 bullet-point summaries
-   Full chat history with timestamps
-   Embedding + vector search via LangChain + ChromaDB

---

## Folder Structure

```bash
├── main.py                    # Streamlit app
├── backend.py                 # Vectorstore + LLM logic
├── utils.py                   # File access utilities
├── vectorstore/               # Auto-generated Chroma embeddings (ignored by git)
├── transparency_hub_documents/
│   └── [company]/privacy/*.txt   # Raw policy text files
├── requirements.txt
├── .env
└── .gitignore
```

The `transparency_hub_documents/` folder contains subfolders by company (e.g., `blackplanet/`) and stores policy files in the `privacy/` subdirectory as `.txt`.

## Setup Instructions

1. Clone the repo

```bash
git clone https://github.com/alaynamnguyen/297R-researchers.git
cd 297R-researchers
```

2. Create your .env file

```bash
touch .env
```

Then paste your OpenAI API key into it:

```env
OPENAI_API_KEY=sk-...
```

3. Install dependencies
   We recommend using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Run the app

```bash
streamlit run main.py
```
