# sqlwriter

## Setup and Run

### 1) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) (Optional) Configure environment
Create a `.env` file in the project root if needed. Useful variables:
```
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Database (choose one approach)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# or individual vars (used when DATABASE_URL is not set)
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dbname

# Vanna memory store
VANNA_CHROMA_DIR=./chroma_db
VANNA_CHROMA_COLLECTION=vanna_memory
```

### 4) Run the server
```bash
python main.py
```

The app will start on http://localhost:8000