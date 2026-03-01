import os
import fitz  # PyMuPDF
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.core.logging import logger

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, file_path: str) -> List[Dict]:
        """Extracts text from PDF with page numbers"""
        doc = fitz.open(file_path)
        pages_content = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages_content.append({
                    "content": text,
                    "page": page_num + 1
                })
        return pages_content

    def process_document(self, file_path: str, document_id: str, user_id: str):
        """Main pipeline: Extract -> Chunk -> Embed -> Store"""
        logger.info(f"Starting RAG pipeline for document {document_id}")
        
        # 1. Extract
        pages = self.extract_text_from_pdf(file_path)
        
        # 2. Chunk
        chunks = []
        metadatas = []
        for page in pages:
            page_chunks = self.text_splitter.split_text(page["content"])
            for chunk in page_chunks:
                chunks.append(chunk)
                metadatas.append({
                    "document_id": str(document_id),
                    "user_id": str(user_id),
                    "page": page["page"],
                    "source": os.path.basename(file_path)
                })

        # 3. Store in ChromaDB
        persist_directory = os.path.join(settings.CHROMA_DB_DIR, str(user_id))
        
        vector_db = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            metadatas=metadatas,
            persist_directory=persist_directory,
            collection_name=f"user_{user_id}_docs"
        )
        
        logger.info(f"Successfully indexed {len(chunks)} chunks for document {document_id}")
        return len(pages)

    def ask_question(self, user_id: str, question: str):
        """Semantic search + LLM generation"""
        persist_directory = os.path.join(settings.CHROMA_DB_DIR, str(user_id))
        
        # Load existing collection
        vector_db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name=f"user_{user_id}_docs"
        )

        # 1. Search for context
        docs = vector_db.similarity_search(question, k=4)
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [
            {"source": doc.metadata.get("source"), "page": doc.metadata.get("page")}
            for doc in docs
        ]

        # 2. Generate Answer with OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = (
            "You are a helpful assistant. Use the following context from uploaded PDF documents "
            "to answer the user's question. If you don't know the answer based on the context, "
            "just say you don't know based on the provided documents. "
            "Be precise and cite the context if possible.\n\n"
            f"CONTEXT:\n{context}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.2
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }

rag_service = RAGService()
