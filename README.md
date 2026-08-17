# Git Helper

## Introduction

Many times you know what you need to do in a GitHub repository but you don't know the exact command(s) to type in. Previously you would go to Google, or just directly StackOverflow to see if the same question had been already asked, or go to websites like [Oh Shit, Git!?!](https://ohshitgit.com/ "https://ohshitgit.com/"), but what if you had an AI assistant that would return the correct `git` command using nothing but natural language. This is what my project is about! :smile:

Using a Streamlit web app interface, you can use natural language to retrieve the correct `git` command for a particular situation. Buttons for user feedback are positioned below each output response. These are used to measure hit rate and average latency. Hit rate over time, mean reciprocal rate over time, average latency in milliseconds and table review of retrieved documents are visualized in a Grafana dashboard.

The knowledge base is generated from the HTML version of the [Pro Git book](https://github.com/progit/progit2/releases/download/2.1.450/progit.html "https://github.com/progit/progit2/releases/download/2.1.450/progit.html") (version 2.1.450) written by Scott Chacon and Ben Straub, which is available online at the [Pro Git website](https://github.com/progit/progit2 "https://github.com/progit/progit2").

## Directory layout

The directory layout of the project is as following:

```text
git-helper/
├── .venv
├── app/
|   ├── monitor.py
│   ├── rag_helper.py
│   └── streamlit_app.py
├── data/
│   ├── embeddings_cache.json
│   └── progit.html
├── ingest/
│   ├── download.py
│   ├── embed.py
│   ├── load_qdrant.py
│   ├── parse.py
│   └── run.py
├── monitoring/
│   ├── grafana/
│   │   └── provisioning/
│   │       └── datasources/
│   │           └── postgres.yml
│   ├── git-helper-dashboard.json
│   ├── docker-compose.yml
│   └── init.sql
├── src/
│   └── git_helper
│       ├── __init__.py
│       └── config.py
├── Makefile
└── README.md
```

## Evaluation

In order to have the Streamlit app running locally in a browser, use the commands in the `Makefile`. First setup the environment locally by running,

```language-bash
> make install
```

This will create a local Python environment using [uv](https://docs.astral.sh/uv/ "https://docs.astral.sh/uv/") and it will install all the dependencies. After that you need to create a [Qdrant](https://cloud.qdrant.io "https://cloud.qdrant.io") account for a free Qdrant cluster instance to host the embeddings created from the book. The Qdrant cluster is accessed locally through the `QDRANT_API_KEY` and `QDRANT_URL` API keys, which need to be saved in a `.env` file in the local repository. Once the API keys are saved, run the following command from `Makefile`,

```language-bash
> make ingest
```

This will download the Pro Git book, split the documents into smaller sections into prose and Git commands, cache the embeddings locally in a Json file and load the embeddings into a Qdrant instance.

To setup the PostgreSQL and Grafana environments, make sure Docker is installed and running in the background, and then run the following from `Makefile`,

```language-bash
> make monitoring-up
```

This command will launch the Docker using the `docker-compose.yml` config. You may access Grafana in a browser at [http://localhost:3000](http://localhost:3000). The instance-agnostic dashboard created in this project is saved in the `monitoring` folder as `git-helper-dashboard.json`, and can be used for sharing externally in another instance.

To stop the monitoring run the command,

```language-bash
> make monitoring-down
```

To launch the Streamlit web app locally just run,

```language-bash
> make app
```

This should automatically open the app in the default browser. Once you have reviewed the project, you may easily remove it by running,

```language-bash
> make clean
```

## Technologies

The project makes use of the following software packages and tools: [Streamlit](https://streamlit.io/ "https://streamlit.io/"), [Qdrant](https://qdrant.tech/ "https://qdrant.tech/"), [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest "https://beautiful-soup-4.readthedocs.io/en/latest"), the [OpenAI Python API library](https://pypi.org/project/openai/ "https://pypi.org/project/openai/"), [Grafana](https://grafana.com/ "https://grafana.com/") [Docker](https://www.docker.com/ "https://www.docker.com/"), [PostgreSQL](https://www.postgresql.org/ "https://www.postgresql.org/") and Python version 3.12.9.
