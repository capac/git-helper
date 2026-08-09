import json
import os
from download import download
from embed import embed_batch
from load_qdrant import load
from parse import parse_book


def main():
    download()

    print("Parsing...")
    records = parse_book("data/progit.html")

    # Split into prose + command docs
    docs = []
    for r in records:
        docs.append({**r, "doc_id": f"{r['section_id']}_prose",
                     "text": r["prose"], "type": "prose"})
        if r["code_blocks"]:
            docs.append(
                {**r, "doc_id": f"{r['section_id']}_commands",
                 "text": "\n".join(r["code_blocks"]), "type": "commands"})

    print(f"Embedding {len(docs)} documents...")
    texts = [d["text"] for d in docs]
    embeddings = []
    for i in range(0, len(texts), 100):
        embeddings.extend(embed_batch(texts[i:i+100]))

    # Cache embeddings locally so you don't re-embed on every run
    with open("data/embeddings_cache.json", "w") as f:
        json.dump({"docs": docs, "embeddings": embeddings}, f)

    print("Loading into Qdrant...")
    load(docs, embeddings,
         url=os.environ["QDRANT_URL"],
         api_key=os.environ["QDRANT_API_KEY"])
    print("Done.")


if __name__ == "__main__":
    main()
