# 🤖 RAG AI Assistant

> A Retrieval-Augmented Generation (RAG) based AI assistant that retrieves relevant information from your documents and generates intelligent, context-aware responses using Large Language Models.
---

## 📖 Overview

RAG AI Assistant allows you to upload your own documents and chat with them intelligently. Instead of relying solely on a language model's pre-trained knowledge, it retrieves the most relevant chunks from your documents first, then generates grounded, accurate answers — reducing hallucinations and keeping responses contextually relevant.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Document Upload** | Upload PDFs and text documents for processing |
| 🔍 **Semantic Search** | Find relevant content using vector similarity search |
| 🧠 **RAG Pipeline** | Retrieval-Augmented Generation for accurate, grounded answers |
| 🤖 **LLM-Powered** | Supports OpenAI and Groq as LLM backends |
| ⚡ **FastAPI Backend** | High-performance async REST API |
| 📚 **Vector Store** | ChromaDB / FAISS for efficient embedding storage |
| 💬 **Conversational UI** | React-based chat interface with Tailwind CSS |
| 🔗 **LangChain Pipeline** | Modular, extensible RAG chain architecture |

---

## 🛠️ Tech Stack

### Backend
- **[Python 3.10+](https://www.python.org/)** — Core language
- **[FastAPI](https://fastapi.tiangolo.com/)** — Async REST API framework

### AI / ML
- **[LangChain](https://www.langchain.com/)** — RAG pipeline orchestration
- **[OpenAI API](https://platform.openai.com/)** / **[Groq API](https://console.groq.com/)** — LLM backends
- **[HuggingFace Embeddings](https://huggingface.co/)** — Document embedding models
- **[ChromaDB](https://www.trychroma.com/)** / **[FAISS](https://faiss.ai/)** — Vector databases

### Storage
- **Vector Database** — Embedding storage and similarity search
- **SQLite** — Metadata and session storage

### Frontend
- **[React.js](https://react.dev/)** — UI framework
- **[Tailwind CSS](https://tailwindcss.com/)** — Utility-first styling

---

## 📂 Project Structure

```
RAG-AI-Assistant/
│
├── app/
│   ├── routes/          # API route handlers (upload, chat, etc.)
│   ├── services/        # Business logic layer
│   ├── rag/             # RAG pipeline (retriever, chain, prompts)
│   ├── utils/           # Helpers and utility functions
│   └── main.py          # FastAPI app entry point
│
├── documents/           # Uploaded source documents
├── vectorstore/         # Persisted vector embeddings
├── requirements.txt     # Python dependencies
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI API key **or** Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/RAG-AI-Assistant.git
cd RAG-AI-Assistant
```

### 2. Set Up the Backend

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Provider — choose one
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Vector Store — "chroma" or "faiss"
VECTOR_STORE=chroma

# Embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# App settings
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 4. Run the Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at `http://localhost:8000`.  
Interactive docs available at `http://localhost:8000/docs`.

### 5. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a document for processing |
| `POST` | `/api/chat` | Send a query and receive a RAG-based response |
| `GET` | `/api/documents` | List all uploaded documents |
| `DELETE` | `/api/documents/{id}` | Remove a document and its embeddings |
| `GET` | `/health` | Health check |

### Example: Chat Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the refund policy?", "top_k": 5}'
```

```json
{
  "answer": "According to the uploaded document, the refund policy allows...",
  "sources": ["policy.pdf — page 3", "policy.pdf — page 7"],
  "confidence": 0.91
}
```

---

## 🧠 How It Works

```
User Query
    │
    ▼
┌─────────────────┐
│  Embed Query    │  ← HuggingFace Embedding Model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Search   │  ← ChromaDB / FAISS
│ (Top-K Chunks)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Prompt   │  ← LangChain PromptTemplate
│ (Context + Q)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Call      │  ← OpenAI / Groq
└────────┬────────┘
         │
         ▼
    Final Answer
```

1. **Ingestion** — Documents are split into chunks, embedded, and stored in the vector store.
2. **Retrieval** — On each query, the top-K most semantically similar chunks are retrieved.
3. **Augmentation** — Retrieved chunks are injected into the LLM prompt as context.
4. **Generation** — The LLM produces a grounded answer based on the retrieved context.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- [LangChain](https://www.langchain.com/) for the RAG framework
- [OpenAI](https://openai.com/) and [Groq](https://groq.com/) for LLM APIs
- [HuggingFace](https://huggingface.co/) for open-source embedding models
- [ChromaDB](https://www.trychroma.com/) for the vector store

---

<p align="center">Built with ❤️ using Python, FastAPI, LangChain & React</p>
