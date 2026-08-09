# Git Commands Using Natural Language

The aim of this project is to create a Streamlit web app interface where one can use natural language to retrieve the correct `git` command for a particular situation. As for documentation, it makes use of the HTML version of the [Pro Git book](https://github.com/progit/progit2/releases/download/2.1.450/progit.html "https://github.com/progit/progit2/releases/download/2.1.450/progit.html") written by Scott Chacon and Ben Straub, and of the [Pro Git manual](https://git-scm.com/docs "https://git-scm.com/docs") which both derive from the [Pro Git website](https://github.com/progit/progit2 "https://github.com/progit/progit2").

## Directory layout

The directory layout of the project is as following:

```text
git-commands-with-natural-language/
├── data/
│   ├── progit.html       # downloaded once
│   └── embeddings_cache.json
├── ingest/
│   ├── download.py
│   ├── embed.py
│   ├── load_qdrant.py
│   ├── parse.py
│   └── run.py            # entrypoint: python -m ingest.run
├── app/
│   ├── rag_helper.py     # RAGBase subclass using Qdrant
│   └── streamlit_app.py
├── .env
├── docker-compose.yml    # optional: qdrant local container
└── requirements.txt
```

## Requirements

The project makes use of the following technologies: [Streamlit](https://streamlit.io/ "https://streamlit.io/"), [Qdrant](https://qdrant.tech/ "https://qdrant.tech/"), [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest "https://beautiful-soup-4.readthedocs.io/en/latest"), the [OpenAI Python API library](https://pypi.org/project/openai/ "https://pypi.org/project/openai/") and Python version 3.12.9.
