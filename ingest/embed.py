from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()


def embed_batch(
        texts: list[str], model="text-embedding-3-small"
        ) -> list[list[float]]:
    texts = [t.replace("\n", " ") for t in texts]
    resp = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in resp.data]
