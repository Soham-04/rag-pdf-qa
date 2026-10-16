"""Run with: python -m streamlit run app.py"""
import hashlib
import streamlit as st
from rag import read_pdf, build_index, answer_question

st.set_page_config(page_title='PaperTrail | PDF Q&A', page_icon='📚', layout='wide')
st.title('📚 PaperTrail')
st.caption('Ask your PDFs. Check the evidence.')
st.info('Local app • No paid API • Text PDFs only. First use downloads the embedding model.')

@st.cache_resource
def load_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

with st.sidebar:
    st.header('Your documents')
    uploads = st.file_uploader('Upload up to 5 PDFs (20 MB each)', type=['pdf'], accept_multiple_files=True)
    model = st.selectbox('Ollama model', ['qwen2.5:1.5b', 'qwen2.5:7b'])
    st.caption('Install and open Ollama, then run: ollama pull ' + model)
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
        if len(uploads) > 5:
            raise ValueError('Upload at most 5 PDFs at a time.')
        with st.spinner('Reading PDFs and building the semantic index…'):
            pages, skipped = [], 0
            for upload in uploads:
                extracted, empty = read_pdf(upload.getvalue(), upload.name)
                pages.extend(extracted)
                skipped += empty
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
            answer, documents = answer_question(st.session_state.index, question, model)
        st.session_state.answer = (question, answer, documents)
    except Exception as exc:
        st.error('Answer generation failed. Make sure Ollama is open and the selected model is downloaded. Try a smaller model if memory is limited.')
        with st.expander('Technical details'):
            st.code(str(exc))
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
