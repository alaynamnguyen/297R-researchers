import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables from .env
load_dotenv()

# --------------------------------------------------------------------
# Load and chunk documents
# --------------------------------------------------------------------
def load_policy_text(text: str, source: str) -> List[Document]:
    return [Document(page_content=text, metadata={"source": source})]

def chunk_documents(documents: List[Document], chunk_size=1000, chunk_overlap=100) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for doc in documents:
        for chunk in splitter.split_text(doc.page_content):
            chunks.append(Document(page_content=chunk, metadata=doc.metadata))
    return chunks

# --------------------------------------------------------------------
# Vector store setup
# --------------------------------------------------------------------
def create_or_load_vectorstore(text: str, source_id: str, persist_dir="vectorstore") -> Chroma:
    os.makedirs(persist_dir, exist_ok=True)
    embeddings = OpenAIEmbeddings()
    vectorstore_path = os.path.join(persist_dir, source_id.replace(".txt", ""))

    if os.path.exists(vectorstore_path):
        return Chroma(
            persist_directory=vectorstore_path,
            embedding_function=embeddings,
            collection_name="privacy_policies"
        )

    docs = load_policy_text(text, source=source_id)
    chunks = chunk_documents(docs)
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=vectorstore_path,
        collection_name="privacy_policies"
    )
    store.persist()
    return store

# --------------------------------------------------------------------
# Question answering chain
# --------------------------------------------------------------------
def get_retrieval_chain(vectorstore: Chroma, temperature=0.2) -> RetrievalQA:
    llm = ChatOpenAI(temperature=temperature)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )

def answer_question(query: str, qa_chain: RetrievalQA) -> Dict[str, Any]:
    result = qa_chain.invoke({"query": query})
    answer = result["result"]
    source_docs = result["source_documents"]
    sources = [doc.page_content.strip() for doc in source_docs]
    return {
        "answer": answer,
        "sources": sources
    }

# --------------------------------------------------------------------
# Summarization
# --------------------------------------------------------------------
def summarize_policy(text: str) -> str:
    llm = ChatOpenAI(temperature=0.0)
    prompt = (
        "Please summarize the privacy policy below in 3–5 bullet points focusing on data collection, use, sharing, and rights.\n"
        f"{text}\n\nSummary:"
    )
    response = llm.invoke(prompt)
    return response.content if hasattr(response, 'content') else str(response)
