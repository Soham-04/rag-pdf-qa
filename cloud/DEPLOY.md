# Deploy the free-tier online demo

Local `app.py` continues to use Ollama. The cloud entry point is `cloud/app.py`.

1. Sign in at https://console.groq.com and create an API key. Stay on the free plan. Never share the key in chat or commit it to GitHub.
2. Sign in at https://share.streamlit.io using GitHub and authorize the repository.
3. Create an app with repository `Soham-04/rag-pdf-qa`, branch `main`, main file path `cloud/app.py`.
4. In Advanced settings select Python `3.11`, then add the following Secrets, privately replacing the placeholder:

```toml
GROQ_API_KEY = "YOUR_REAL_KEY"
GROQ_MODEL = "openai/gpt-oss-20b"
```

5. Deploy. The requirements file next to the cloud entry point provides cloud dependencies. First startup downloads the embedding model. Copy the actual `.streamlit.app` URL after success.
6. Upload a short non-sensitive PDF, ask a known fact, and check page evidence. Test an unrelated question too. Open the URL on a phone after stopping the laptop app to verify independence from the laptop.

## Online behavior

FastEmbed uses the Hugging Face `BAAI/bge-small-en-v1.5` model with ONNX. FAISS performs retrieval. Groq generates answers. This reduces cloud dependencies by avoiding PyTorch and local LLM hosting.

The online demo allows 2 PDFs, 5 MB per file, and 100 total pages. PDFs and indexes are held in hosting session memory, not intentionally written to disk. Questions and retrieved excerpts are sent to Groq. Do not upload confidential material.

All visitors share the server-side key and its quota. No custom global limiter is implemented; provider free-tier limits enforce the quota. Stay on the free plan and do not enable paid billing for this demo. Free services may sleep, change limits or model availability, or refuse deployment. This is a portfolio demo, not an availability guarantee.

## Validation

Python syntax and the existing offline extraction tests were checked. Cloud installation, embedding download, Groq requests and deployment still need a hosted smoke test after secrets are configured. No live URL is claimed by this change.
