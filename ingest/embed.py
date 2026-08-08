from dotenv import load_dotenv, find_dotenv
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
from openai import OpenAI  # noqa: E402
import tiktoken  # noqa: E402

EMBED_MODEL = "text-embedding-3-small"
MAX_TOKENS = 8000   # leave a small buffer below the 8192 hard limit

client = OpenAI()
_enc = tiktoken.get_encoding("cl100k_base")


def _truncate(text: str) -> str:
    """Truncate text to MAX_TOKENS tokens,
    preserving whole words where possible."""
    tokens = _enc.encode(text)
    if len(tokens) <= MAX_TOKENS:
        return text
    return _enc.decode(tokens[:MAX_TOKENS])


def embed_batch(
        texts: list[str],
        model: str = EMBED_MODEL
        ) -> list[list[float]]:
    texts = [_truncate(t.replace("\n", " ")) for t in texts]
    resp = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in resp.data]
