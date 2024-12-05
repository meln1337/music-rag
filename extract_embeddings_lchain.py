from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import torch

from history.config import PINECONE_API_KEY
from langchain_huggingface import HuggingFaceEmbeddings
from splitter import split_documents
import time
from pinecone_text.sparse import BM25Encoder
from langchain_community.retrievers import (
    PineconeHybridSearchRetriever,
)

# Example: Filter stopwords to reduce vocabulary size


EMBEDDING_DIM = 768
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

pc = Pinecone(api_key=PINECONE_API_KEY)

# pc.configure_index(name='rag-llm', deletion_protection='disabled')
# pc.delete_index(name='rag-llm')



embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

index_name = "rag-llm"
namespace = "embedded-texts"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=EMBEDDING_DIM,
        metric='dotproduct',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

    print('Index has been created!')

index = pc.Index(index_name)

print('Connected to the index')

# view index stats
index.describe_index_stats()

documents, texts, ids = split_documents()

metadatas = [doc['metadata'] for doc in documents]

# print(texts)
print(len(texts))
print(len(documents))
print(len(ids))

bm25 = BM25Encoder()
bm25.fit(texts)

bm25.dump("sparse_encoder.json")
bm25 = BM25Encoder().load("sparse_encoder.json")

vector_store = PineconeHybridSearchRetriever(
    index=index,
    embeddings=embedding,
    sparse_encoder=bm25,
    namespace=namespace)


vector_store.add_texts(texts=texts,
                        ids=ids,
                        metadatas=metadatas,
                        namespace=namespace)