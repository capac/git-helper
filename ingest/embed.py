from dotenv import load_dotenv, find_dotenv
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
from openai import OpenAI  # noqa: E402

client = OpenAI()


def embed_batch(
        texts: list[str], model="text-embedding-3-small"
        ) -> list[list[float]]:
    texts = [t.replace("\n", " ") for t in texts]
    resp = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in resp.data]
