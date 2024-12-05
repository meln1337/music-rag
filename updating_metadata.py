from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import torch

from history.config import PINECONE_API_KEY
from splitter import split_documents
import time
from tqdm import tqdm


EMBEDDING_DIM = 768
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

pc = Pinecone(api_key=PINECONE_API_KEY)

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
print(index.describe_index_stats())

documents, texts, ids = split_documents()

batch_size = 128

for idx in tqdm(range(0, len(ids))):
    index.update(id=ids[idx], set_metadata={
        "id": ids[idx],
    }, namespace=namespace)