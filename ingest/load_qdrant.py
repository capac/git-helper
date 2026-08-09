from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

COLLECTION = "progit"
DIM = 1536  # text-embedding-3-small


# ingest/load_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
import uuid

COLLECTION = "progit"
DIM = 1536  # text-embedding-3-small

def load(
        docs: list[dict],
        embeddings: list[list[float]],
        url: str,
        api_key: str
        ):
    client = QdrantClient(url=url, api_key=api_key)

    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, doc["doc_id"])),
            vector=emb,
            payload=doc,
        )
        for doc, emb in zip(docs, embeddings)
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    # Required for filtering by doc type (strict mode rejects unindexed fields)
    client.create_payload_index(COLLECTION, "type", PayloadSchemaType.KEYWORD)
    print(f"Loaded {len(points)} documents.")