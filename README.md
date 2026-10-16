# PaperTrail — RAG PDF Question Answering

An educational Streamlit application that retrieves PDF passages using semantic embeddings and FAISS, then asks a local language model to answer with excerpt references. No paid API key is required.

## Features

- Up to five text-based PDFs, 20 MB and 200 pages per file.
- Page-aware extraction, overlapping chunks, Hugging Face embeddings and FAISS similarity search.
- Local answer generation through Ollama and LangChain.
- Expandable retrieved passages with filenames and original page numbers.
- Download an answer with its evidence; clear the session when finished.
- Scanned and password-protected PDFs produce clear errors; blank pages are skipped.

## Windows setup — start here

1. Install **Python 3.11** from https://www.python.org/downloads/ (enable Add Python to PATH).
2. Install **Ollama** from https://ollama.com/download and open it.
3. Open Command Prompt and download the small model:

```bat
ollama pull qwen2.5:1.5b
```

4. Extract this project. Open Command Prompt in the folder containing `app.py` and run these commands, one at a time:

```bat
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

5. Open the local URL printed in the terminal (normally http://localhost:8501). Upload a PDF, click **Process PDFs**, then ask a question.
6. For later runs, keep Ollama open and double-click `START_WINDOWS.bat`.

Internet is needed for package and model downloads. Inference runs locally after downloads. Start with one short English PDF. CPU speed and available RAM determine performance; the small model can make mistakes. The 7B option is more demanding and must be downloaded separately.

On macOS/Linux, create the environment using `python3 -m venv .venv`, then replace `.venv\Scripts\python.exe` with `.venv/bin/python` in the commands above.

## How it works

1. `read_pdf()` in `rag.py` uses pypdf to extract text and retain source page numbers.
2. `build_index()` splits text into 700-character chunks with 120-character overlap. Overlap reduces the chance that a sentence crossing a boundary loses its context.
3. `all-MiniLM-L6-v2` converts chunks into normalized numeric vectors. FAISS holds these vectors in memory.
4. `answer_question()` embeds the question and retrieves the four nearest chunks.
5. A LangChain prompt sends the question and retrieved text to a local Ollama model. The model is instructed to use only the excerpts and cite them.
6. `app.py` renders the answer and the retrieved evidence in Streamlit.

RAG adds retrieved context at inference time; it does not train the LLM on your PDFs. FAISS is the chosen vector index; ChromaDB is an alternative and is not used here. Questions are independent, not a conversational memory chain.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Uploads, session state, model selection, questions and answer display |
| `rag.py` | Extraction, chunking, index building, retrieval and generation |
| `requirements.txt` | Python dependencies |
| `START_WINDOWS.bat` | Launch an already installed app |
| `tests/test_pdf.py` | Offline extraction and validation checks |
| `VALIDATION.md` | What has and has not been tested |

## Manual acceptance checks

Use a short PDF with known facts and ask for one of those facts. Check the answer and its page reference. Ask something absent from the PDF and check that the model admits it cannot find the answer. Small LLMs may fail this check; the prompt is not a guarantee.

Upload a scan to verify the OCR error. Replace the selected PDF and verify questions are disabled until reprocessing. Stop Ollama and verify the actionable generation error. Clear documents and check that the previous answer disappears.

## Get the source

Repository: https://github.com/Soham-04/rag-pdf-qa

Choose **Code → Download ZIP**, extract the folder, and follow the Windows setup above.
If Git is installed, you can also use:

```bash
git clone https://github.com/Soham-04/rag-pdf-qa.git
cd rag-pdf-qa
```

Do not commit virtual environments, private PDFs, model files or secrets.

## Hosting

This version runs on your computer. Uploading source to GitHub does not host Streamlit. GitHub Pages hosts static content and cannot run this Python backend. An online deployment of this particular version needs a reachable Ollama service; a hosted Streamlit server cannot use your laptop's `localhost`. No online deployment is included. A separate CPU-hosted model or quota-limited free provider can be evaluated for a later hosted version; free capacity is not guaranteed.

## Limitations and privacy

PDFs and their index stay in the local Streamlit session; the app does not intentionally write them to disk. Model files are cached on the computer. Clearing the session removes app references, not guaranteed secure memory erasure. Do not expose this educational app publicly without resource controls and access controls.

OCR, robust table extraction, multilingual evaluation and automatic citation verification are not implemented. Similarity search always returns nearest passages even for unrelated questions. The model can hallucinate or follow malicious document instructions despite its prompt; inspect the evidence. No accuracy claim is made.

## Reference documentation

- https://docs.langchain.com/oss/python/integrations/embeddings/sentence_transformers
- https://docs.langchain.com/oss/python/integrations/providers/ollama/
- https://ollama.com/library/qwen2.5:1.5b
