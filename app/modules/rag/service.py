import os
import fitz  # PyMuPDF
import traceback
from app.core.config import settings
from typing import List, Dict, Optional, Generator, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from app.core.logging import logger
from openai import OpenAI

# CRITICAL: Set environment variable globally for LangChain components
if settings.PINECONE_API_KEY:
    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        if settings.USE_PINECONE:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index_name = settings.PINECONE_INDEX_NAME

    def extract_text_from_pdf(self, file_path: str) -> List[Dict]:
        logger.info(f"Worker: Extracting text from {file_path}")
        doc = fitz.open(file_path)
        pages_content = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages_content.append({"content": text, "page": page_num + 1})
        return pages_content

    def process_document(self, file_path: str, document_id: str, user_id: str, original_filename: str):
        try:
            pages = self.extract_text_from_pdf(file_path)
            
            all_chunks = []
            all_metadatas = []
            
            for page in pages:
                page_chunks = self.text_splitter.split_text(page["content"])
                for chunk in page_chunks:
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "document_id": str(document_id),
                        "user_id": str(user_id),
                        "page": page["page"],
                        "source": original_filename
                    })

            if not all_chunks:
                return len(pages)

            if settings.USE_PINECONE:
                logger.info(f"Worker: Sending {len(all_chunks)} chunks to Pinecone...")
                # The environment variable is now set, so it should find the key automatically
                PineconeVectorStore.from_texts(
                    texts=all_chunks,
                    embedding=self.embeddings,
                    metadatas=all_metadatas,
                    index_name=self.index_name,
                    namespace=f"user_{user_id}"
                )
            else:
                persist_directory = os.path.join(settings.CHROMA_DB_DIR, str(user_id))
                Chroma.from_texts(
                    texts=all_chunks,
                    embedding=self.embeddings,
                    metadatas=all_metadatas,
                    persist_directory=persist_directory,
                    collection_name=f"user_{user_id}_docs"
                )
            
            logger.info(f"Worker: Successfully indexed {original_filename}")
            return len(pages)
        except Exception as e:
            logger.error(f"Worker Error in process_document: {str(e)}")
            raise e

    def delete_document_vectors(self, user_id: str, document_id: str):
        try:
            if settings.USE_PINECONE:
                index = self.pc.Index(self.index_name)
                stats = index.describe_index_stats()
                target_ns = f"user_{user_id}"
                if target_ns in stats.get('namespaces', {}):
                    index.delete(filter={"document_id": str(document_id)}, namespace=target_ns)
            else:
                persist_directory = os.path.join(settings.CHROMA_DB_DIR, str(user_id))
                vector_db = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=f"user_{user_id}_docs"
                )
                vector_db.delete(where={"document_id": str(document_id)})
        except Exception as e:
            logger.warning(f"Vector delete skipped: {str(e)}")

    def ask_question_stream(
        self, 
        user_id: str, 
        question: str, 
        selected_document_ids: Optional[List[str]] = None,
        chat_history: Optional[List[Dict]] = None,
        doc_id_to_name: Optional[Dict[str, str]] = None
    ) -> Tuple[Generator[str, None, None], List[Dict]]:
        
        if settings.USE_PINECONE:
            vector_db = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=f"user_{user_id}"
            )
        else:
            persist_directory = os.path.join(settings.CHROMA_DB_DIR, str(user_id))
            vector_db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings,
                collection_name=f"user_{user_id}_docs"
            )

        search_kwargs = {}
        if selected_document_ids:
            search_kwargs["filter"] = {"document_id": {"$in": [str(sid) for sid in selected_document_ids]}}

        RELEVANCE_THRESHOLD = 0.38
        docs_with_scores = vector_db.similarity_search_with_score(question, k=5, **search_kwargs)
        
        filtered_docs = [doc for doc, score in docs_with_scores if score < RELEVANCE_THRESHOLD]

        context_parts = []
        sources = []
        seen_sources = set()

        if filtered_docs:
            for doc in filtered_docs:
                doc_id = doc.metadata.get("document_id")
                page = doc.metadata.get("page")
                source_name = doc_id_to_name.get(doc_id) if doc_id_to_name and doc_id in doc_id_to_name else doc.metadata.get("source")
                context_parts.append(f"SOURCE: {source_name}\nCONTENT: {doc.page_content}")
                src_key = f"{doc_id}_{page}"
                if src_key not in seen_sources:
                    sources.append({"source": source_name, "page": page, "document_id": doc_id})
                    seen_sources.add(src_key)
        
        context_string = "\n\n".join(context_parts) if context_parts else ""
        is_context_empty = len(context_parts) == 0

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        if is_context_empty:
            system_prompt = (
                "You are a strict Document Assistant. The user's question is NOT related to the selected documents."
            )
        else:
            system_prompt = (
                "You are a Document Analysis Expert. Use ONLY the provided context below to answer. \n\n"
                f"CONTEXT:\n{context_string}"
            )

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        def generate():
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.0,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return generate(), sources

rag_service = RAGService()
