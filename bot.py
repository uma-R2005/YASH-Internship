import os
from dotenv import load_dotenv
from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.embeddings import BaseEmbedding
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from huggingface_hub import InferenceClient
from typing import List

load_dotenv()

class HFEmbedding(BaseEmbedding):
    def __init__(self, token: str):
        super().__init__()
        self._token = token
        self._client = InferenceClient(token=token)

    def _get_text_embedding(self, text: str) -> List[float]:
        result = self._client.feature_extraction(
            text,
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        if hasattr(result, 'tolist'):
            vec = result.tolist()
        else:
            vec = result
        if isinstance(vec[0], list):
            vec = vec[0]
        return vec

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._get_text_embedding(t) for t in texts]


def load_bot():

    print("="*50)
    print("LOADING MISTRAL-7B BOT")
    print("="*50)

    token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    print("\n[1/3] Loading Embeddings...")
    embed_model = HFEmbedding(token=token)
    Settings.embed_model = embed_model
    print("Embeddings ready")

    print("\n[2/3] Loading FAISS Index...")
    storage_context = StorageContext.from_defaults(
        persist_dir="storage"
    )
    index = load_index_from_storage(storage_context)
    print("FAISS loaded")

    print("\n[3/3] Connecting Mistral-7B...")
    llm = HuggingFaceInferenceAPI(
        model_name="mistralai/Mistral-7B-Instruct-v0.2",
        token=token,
        temperature=0.2,
        max_new_tokens=1024,
        timeout=60,
    )
    Settings.llm = llm
    print("Mistral-7B connected!")

    # Using query_engine - NO chat_engine, NO memory, NO reranker
    # This is the simplest and most reliable approach
    query_engine = index.as_query_engine(
        similarity_top_k=5,
        verbose=False,
    )

    print("\nBot Ready!")
    print("="*50)

    return query_engine, index