import os
from llama_index.core import StorageContext, VectorStoreIndex, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from sqlalchemy import text
from app.database import engine
import psycopg2

class RAGEngine:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        self.llm = Ollama(model="llama3", base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"))
        self.vector_store = None
        self.index = None

    async def initialize(self):
        # Setup PGVectorStore
        # Note: In a real scenario, we'd parse the DB URL correctly
        db_name = "odoo"
        host = "db"
        password = "odoo"
        user = "odoo"
        port = "5432"

        self.vector_store = PGVectorStore.from_params(
            database=db_name,
            host=host,
            password=password,
            port=port,
            user=user,
            table_name="odoo_embeddings",
            embed_dim=1024, # BGE-M3 dimension
        )
        
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # Initialize an empty index if no documents exist yet
        # or load existing one
        self.index = VectorStoreIndex.from_documents(
            [], storage_context=storage_context, embed_model=self.embedding_model
        )

    async def index_data(self, table_name: str, column_names: list[str]):
        async with engine.connect() as conn:
            columns_str = ", ".join(column_names)
            result = await conn.execute(text(f"SELECT {columns_str} FROM {table_name}"))
            rows = result.fetchall()
            
            documents = []
            for row in rows:
                content = " ".join([f"{col}: {val}" for col, val in zip(column_names, row)])
                documents.append(Document(text=content, metadata={"table": table_name}))
            
            for doc in documents:
                self.index.insert(doc)
            
            return len(documents)

    async def query(self, prompt: str):
        query_engine = self.index.as_query_engine(llm=self.llm)
        response = query_engine.query(prompt)
        return str(response)
