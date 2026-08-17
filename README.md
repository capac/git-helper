# Git Helper

## Introduction

Many times you know what you need to do in a GitHub repository but you don't know the exact command(s) to type in. Previously you would go to Google, or just directly StackOverflow to see if the same question had been already asked, or go to websites like [Oh Shit, Git!?!](https://ohshitgit.com/ "https://ohshitgit.com/"), but what if you had an AI assistant that returns the correct `git` command using nothing but natural language. This is what my project is about! :smile:

Using a Streamlit web app interface, you can use natural language to retrieve the correct `git` command for a particular situation. Buttons for user feedback are positioned below each output response. These are used to measure hit rate and average latency which are present in the lower left-hand corner of the  web app. Below is an image of the web app to give you an idea of what it looks like.

<p align="center">
    <img src="images/streamlit-web-app.png" alt="Streamlit web app" width="800" style="center"/>
</p>

<p align="center" style="font-size: 0.9em;">
<small>Image of Streamlit Git Helper web app.</small>
</p>

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
├── images/
│   ├── grafana-dashboard.png
│   └── streamlit-web-app.png
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

This will create a local Python environment using [uv](https://docs.astral.sh/uv/ "https://docs.astral.sh/uv/") which will also install all of the dependencies.

After that you need to create a [Qdrant](https://cloud.qdrant.io "https://cloud.qdrant.io") account for a free Qdrant cluster instance to host the embeddings created from the book. The Qdrant cluster is accessed locally through the `QDRANT_API_KEY` and `QDRANT_URL` API keys, which need to be saved in a `.env` file in the root of the local directory. For the agentic RAG part of the project you will need an Open AI API key, to be saved in the `.env` file and accessed through the `OPENAI_API_KEY` variable. This will require purchasing at least $5 of OpenAI credit. You also need to save the following line in the `.env` file for PostgreSQL,

```language-bash
POSTGRES_URL=postgresql://githelper:githelper@localhost:5432/githelper
```

Once the API keys are saved, run the following command from `Makefile`,

```language-bash
> make ingest
```

This will download the Pro Git book, split the documents into smaller sections of prose and `git` commands, cache the embeddings locally in a JSON file and upload the embeddings into the Qdrant instance.

To setup the PostgreSQL and Grafana environments, make sure Docker is installed and running in the background, and then run the following `Makefile` command,

```language-bash
> make monitoring-up
```

This command will launch Docker using the `docker-compose.yml` config. You may access Grafana in a browser at [http://localhost:3000](http://localhost:3000). The instance-agnostic dashboard created in this project is saved in the `monitoring` folder as `git-helper-dashboard.json` and can be loaded into Grafana. Below is the image of the Grafana dashboard running for several days with hit rate over time, mean reciprocal rank over time, average latency in milliseconds and the table review of retrieved documents.

<p align="center">
    <img src="images/grafana-dashboard.png" alt="Grafana dashboard" width="800" style="center"/>
</p>

<p align="center" style="font-size: 0.9em;">
  Image of Grafana dashboard with hit rate over time, mean reciprocal rank over time, average latency in milliseconds and the table review of retrieved documents.
</p>

To launch the Streamlit web app locally just run,

```language-bash
> make app
```

This should automatically open the app in the default browser. To stop the Grafana monitoring run the command,

```language-bash
> make monitoring-down
```

Once you have completed reviewing the project, you may easily remove it by running,

```language-bash
> make clean
```

## Technologies

The project makes use of the following software packages and tools: [Streamlit](https://streamlit.io/ "https://streamlit.io/"), [Qdrant](https://qdrant.tech/ "https://qdrant.tech/"), [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest "https://beautiful-soup-4.readthedocs.io/en/latest"), the [OpenAI Python API library](https://pypi.org/project/openai/ "https://pypi.org/project/openai/"), [Grafana](https://grafana.com/ "https://grafana.com/"), [Docker](https://www.docker.com/ "https://www.docker.com/"), [PostgreSQL](https://www.postgresql.org/ "https://www.postgresql.org/") and Python version 3.12.9.
