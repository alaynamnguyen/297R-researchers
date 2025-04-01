import os
from typing import List, Dict, Any, Optional
import uuid

# LangChain imports
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# To set OPENAI_API_KEY environmental variable manually:
# os.environ["OPENAI_API_KEY"] = "key"

###############################################################################
# 1) LOAD & CHUNK DOCUMENTS
###############################################################################
def load_documents(directory: str) -> List[Document]:
    """
    Loads all text files from the specified directory as LangChain Document objects.
    Each Document has .page_content and .metadata.
    """
    docs = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            # Metadata can store policy name, ID, etc.
            metadata = {
                "source": filename
            }
            docs.append(Document(page_content=text, metadata=metadata))
    return docs


def chunk_documents(documents: List[Document], chunk_size=1000, chunk_overlap=100) -> List[Document]:
    """
    Splits documents into smaller chunks for better embedding and retrieval.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunked_docs = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            # Retain original metadata (e.g., source) in each chunk
            chunked_docs.append(
                Document(page_content=chunk, metadata=doc.metadata)
            )
    return chunked_docs


###############################################################################
# 2) BUILD OR UPDATE A VECTOR STORE
###############################################################################
def create_or_load_vectorstore(policies_dir: str,
                               persist_directory: str = "vectorstore") -> Chroma:
    """
    Loads existing Chroma vector store if present. Otherwise, creates one from
    the text files in `policies_dir`.
    """
    embedding_function = OpenAIEmbeddings()
    
    # If there is an existing vectorstore, load it using the below:
    #   vectorstore = Chroma(persist_directory=persist_directory,
    #                        embedding_function=embedding_function)
    # TODO: check if the folder/vectorstore exists and only build if needed.
    
    # Load and chunk the documents
    docs = load_documents(policies_dir)
    chunked_docs = chunk_documents(docs)
    
    # Create a new Chroma store with the chunked docs
    vectorstore = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embedding_function,
        persist_directory=persist_directory
    )
    
    # Persist so that you can reload without re-embedding
    vectorstore.persist()
    
    return vectorstore


###############################################################################
# 3) CHATBOT / Q&A
###############################################################################
def get_retrieval_chain(vectorstore: Chroma, temperature: float = 0.2) -> RetrievalQA:
    """
    Creates a retrieval-based QA chain that returns sources.
    """
    llm = ChatOpenAI(temperature=temperature)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )
    return qa_chain


def answer_question(query: str, qa_chain: RetrievalQA) -> Dict[str, Any]:
    """
    Answers a user query with context from the vector store. Returns both the answer
    and the source documents (for citations).
    """
    result = qa_chain({"query": query})
    answer = result["result"]
    source_docs = result["source_documents"]
    sources = [doc.metadata.get("source", "") for doc in source_docs]
    return {
        "answer": answer,
        "sources": list(set(sources))  # unique source filenames
    }


###############################################################################
# 4) VERIFY LLM ACCURACY
###############################################################################
def verify_answer_with_sources(answer: str, source_docs: List[Document]) -> bool:
    """
    Stub function that attempts to verify if the LLM’s answer is supported by
    the content in source_docs.
    """
    # TODO Pseudocode:
    # 1. Combine source_docs into a single text
    # 2. Possibly run an additional chain that checks if `answer` is consistent
    #    with the combined source text.
    # 3. Return a boolean or a confidence score
    # We are currently bypassing this method for now in main, will revisit to see if we need
    return True


###############################################################################
# 5) SUMMARIZE POLICIES
###############################################################################
def summarize_text(text: str) -> str:
    """
    Summarizes a block of text using an LLM. 
    Could also create a chain from LangChain’s built-in summarization.
    """
    llm = ChatOpenAI(temperature=0.0)
    prompt = (
        "Please provide a concise summary of the following privacy policy text:\n\n"
        f"{text}\n\n"
        "Summary:"
    )
    response = llm.predict(prompt)
    return response.strip()


def summarize_policy_file(filepath: str) -> str:
    """
    Load a single policy file and return its summary.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return summarize_text(text)


###############################################################################
# 6) MAPPING ACROSS REGULATIONS (Skeleton)
###############################################################################
REGULATIONS = {
    "GDPR": ["data subject rights", "EU", "consent", "erasure", "export"],
    "CCPA": ["California", "sale of personal data", "opt-out", "household data"],
    "HIPAA": ["medical", "health information", "patient", "PHI"]
    # Extend as needed
}


def map_policy_to_regulations(text: str) -> List[str]:
    """
    Check for keywords in the text to see if it might relate
    to GDPR, CCPA, HIPAA, etc. In production, use a more robust approach (LLM-based).
    """
    matched = []
    lower_text = text.lower()
    for reg, keywords in REGULATIONS.items():
        for kw in keywords:
            if kw.lower() in lower_text:
                matched.append(reg)
                break
    return matched


###############################################################################
# 7) ADDING / REMOVING POLICIES
###############################################################################
def add_policy_to_store(filepath: str, vectorstore: Chroma) -> None:
    """
    Adds a new policy to the existing vector store.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    new_doc = Document(page_content=text, metadata={"source": filepath})
    text_splitter = RecursiveCharacterTextSplitter()
    chunks = text_splitter.split_text(new_doc.page_content)
    chunk_docs = [Document(page_content=chunk, metadata=new_doc.metadata) for chunk in chunks]

    # Add to vector store
    vectorstore.add_documents(chunk_docs)
    vectorstore.persist()


def remove_policy_from_store(policy_source: str, vectorstore: Chroma) -> None:
    """
    Removes all documents that match a specific 'source' metadata from the store.
    This might require storing doc_ids or unique IDs. Below is a naive approach.
    """
    # TODO: Track doc_ids when documents are added so that we can remove documents from Chroma using doc_ids
    pass
