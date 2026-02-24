import os
import time
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import BaseEmbedding
from huggingface_hub import InferenceClient
from typing import List

load_dotenv()

class HFEmbedding(BaseEmbedding):
    def __init__(self, token: str):
        super().__init__()
        self._token = token
        self._client = InferenceClient(token=token)

    def _get_text_embedding(self, text: str) -> List[float]:
        for attempt in range(3):
            try:
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
            except Exception as e:
                if attempt < 2:
                    print("  Retry " + str(attempt+1) + "/3...")
                    time.sleep(3)
                else:
                    raise e

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._get_text_embedding(t) for t in texts]


def ingest(pdf_path: str):

    print("="*50)
    print("MISTRAL RAG - INGESTION PIPELINE")
    print("="*50)

    print("\n[1/4] Loading PDF...")
    reader = SimpleDirectoryReader(input_files=[pdf_path])
    documents = reader.load_data()
    print("Pages loaded: " + str(len(documents)))

    print("\n[2/4] Splitting into Chunks...")
    splitter = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=100
    )
    nodes = splitter.get_nodes_from_documents(documents)
    print("Total chunks: " + str(len(nodes)))

    print("\n[3/4] Converting to Vectors...")
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    embed_model = HFEmbedding(token=token)
    Settings.embed_model = embed_model

    sample = embed_model.get_text_embedding(nodes[0].text)
    print("Vector dimensions: " + str(len(sample)))

    print("\n[4/4] Storing in FAISS...")
    index = VectorStoreIndex(
        nodes,
        embed_model=embed_model,
        show_progress=True
    )
    os.makedirs("storage", exist_ok=True)
    index.storage_context.persist(persist_dir="storage")
    print("Total vectors stored: " + str(len(nodes)))
    print("FAISS saved to storage/")

    print("="*50)
    print("VECTOR DATABASE IS READY")
    print("="*50)

    return index, len(nodes)


if __name__ == "__main__":
    start = time.time()
    index, total = ingest("RFP_Infra_DOMO.pdf")
    print("Done in: " + str(round(time.time()-start, 2)) + "s")
    print("Total vectors: " + str(total))