# Git Helper

## Introduction

Many times you know what you need to do for a GitHub repository but you don't know the exact command to type in. Previously you would go to StackOverflow and see if the same question had been already asked, or go to websites like [Oh Shit, Git!?!](https://ohshitgit.com/ "https://ohshitgit.com/"), but what if you had an AI assistant that would return the correct `git` command using nothing but natural language. This is what my project is about! :smile:

Using a Streamlit web app interface, you can use natural language to retrieve the correct `git` command for a particular situation. As for the documentation, it makes use of the HTML version of the [Pro Git book](https://github.com/progit/progit2/releases/download/2.1.450/progit.html "https://github.com/progit/progit2/releases/download/2.1.450/progit.html") written by Scott Chacon and Ben Straub, which derives from the [Pro Git website](https://github.com/progit/progit2 "https://github.com/progit/progit2").

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
