"""Run with: python -m streamlit run app.py"""
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from rag import read_pdf, build_index, answer_question

st.set_page_config(page_title='PaperTrail | PDF Q&A', page_icon='📚', layout='wide')
st.title('📚 PaperTrail')
st.caption('Ask your PDFs. Check the evidence.')
st.info('Online demo • Free-tier usage limits apply • Text PDFs only')
st.caption('PDFs are processed on the hosting server. Your question and retrieved passages are sent to Groq. Do not upload confidential documents.')
try:
    api_key = st.secrets.get('GROQ_API_KEY', '')
    model = st.secrets.get('GROQ_MODEL', 'openai/gpt-oss-20b')
except FileNotFoundError:
    api_key, model = '', 'openai/gpt-oss-20b'
if not api_key:
    st.warning('The app owner needs to configure GROQ_API_KEY in Streamlit secrets.')
    st.stop()

@st.cache_resource
def load_embeddings():
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
    return FastEmbedEmbeddings(model_name='BAAI/bge-small-en-v1.5', threads=2)

with st.sidebar:
    st.header('Your documents')
    uploads = st.file_uploader('Upload up to 2 PDFs (5 MB each)', type=['pdf'], accept_multiple_files=True)
    st.caption('Powered by Groq. The demo may pause when its free quota is reached.')
    build = st.button('Process PDFs', type='primary', disabled=not uploads)
    if st.button('Clear documents and answers'):
        st.session_state.clear()
        st.rerun()
    st.markdown('Answers may be wrong. Always check the retrieved pages.')

signature = hashlib.sha256(b''.join(u.name.encode() + hashlib.sha256(u.getvalue()).digest() for u in uploads)).hexdigest() if uploads else None
# Disable questions immediately if the selected documents change.
ready = signature is not None and signature == st.session_state.get('signature')
if build:
    st.session_state.pop('index', None)
    st.session_state.pop('signature', None)
    st.session_state.pop('answer', None)
    ready = False
    try:
        if len(uploads) > 2:
            raise ValueError('Upload at most 2 PDFs at a time.')
        with st.spinner('Reading PDFs and building the semantic index…'):
            pages, skipped = [], 0
            for upload in uploads:
                if upload.size > 5 * 1024 * 1024:
                    raise ValueError('Online demo: each PDF must be smaller than 5 MB.')
                extracted, empty = read_pdf(upload.getvalue(), upload.name)
                pages.extend(extracted)
                skipped += empty
                if len(pages) + skipped > 100:
                    raise ValueError('Online demo: upload at most 100 pages in total.')
            index, count = build_index(pages, load_embeddings())
            st.session_state.update(index=index, signature=signature, chunks=count)
        ready = True
        st.success(f'Indexed {len(pages)} text pages into {count} chunks.')
        if skipped:
            st.warning(f'{skipped} pages contained no extractable text and were skipped. OCR is not included.')
    except Exception as exc:
        st.error(f'Could not process documents: {exc}')

if not ready:
    st.caption('Upload your PDFs and click Process PDFs to begin.')
question = st.text_input('What would you like to know?', placeholder='What are the main findings?', max_chars=2000, disabled=not ready)
if st.button('Find answer', disabled=not ready or not question.strip()):
    st.session_state.pop('answer', None)
    try:
        with st.spinner('Finding evidence and generating an answer…'):
            answer, documents = answer_question(st.session_state.index, question, model, provider='groq', api_key=api_key)
        st.session_state.answer = (question, answer, documents)
    except Exception as exc:
        st.error('Answer generation failed. The free quota may be reached or the service unavailable. Try later; the owner should also check the key and model settings.')
        # Do not show provider errors or server configuration to visitors.
if ready and 'answer' in st.session_state:
    asked, answer, documents = st.session_state.answer
    st.subheader('Answer')
    st.caption(asked)
    st.markdown(answer)
    st.subheader('Retrieved evidence')
    st.caption('These are retrieved passages, not independent proof that every answer claim is correct.')
    for i, document in enumerate(documents, 1):
        with st.expander(f'[{i}] {document.metadata["source"]} · page {document.metadata["page"]}'):
            st.text(document.page_content)
    st.download_button('Download answer', f'Question: {asked}\n\n{answer}\n\nEvidence:\n' + '\n\n'.join(f'[{i}] {d.metadata["source"]}, page {d.metadata["page"]}\n{d.page_content}' for i, d in enumerate(documents, 1)), 'pdf-answer.txt')
