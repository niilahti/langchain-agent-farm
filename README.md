# LangGraph Agent Farm

Built by **Jussi Niilahti**

A small multi-step agent workflow built with **LangGraph** and free large language models via [OpenRouter](https://openrouter.ai).

Instead of a single straight pipeline, this version keeps an explicit shared state and allows the analyst to send the researcher back for one or more revision rounds.

---

## What This Project Does

The workflow has three logical stages:

- **Researcher:** writes a short report about the topic
- **Analyst:** reviews the report, scores it, and decides whether it passes or needs revision
- **Finalizer:** writes a short final summary of the whole run

If the analyst returns `REVISE`, the graph loops back to the researcher with the analyst's feedback.

That is the main reason LangGraph is actually useful here: the workflow is no longer just `step 1 -> step 2`, but a small state machine with conditional routing.

---

## Requirements

- Python 3.9+
- An OpenRouter API key

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/langchain-agent-farm.git
cd langchain-agent-farm
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

Packages used:

- `httpx` for HTTP requests to OpenRouter
- `python-dotenv` for loading environment variables from `.env`
- `langgraph` for building the stateful multi-step workflow

---

## Configuration

### 1. Create an OpenRouter account

Go to [https://openrouter.ai](https://openrouter.ai) and sign up.

### 2. Create an API key

Go to [https://openrouter.ai/keys](https://openrouter.ai/keys), click **Create key**, and copy the generated key.

The key usually starts with:

```text
sk-or-v1-
```

### 3. Create a `.env` file

Create a `.env` file in the project root with this structure:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Important:

- Do not use quotes
- Do not add spaces around `=`
- Do not commit `.env` to Git

---

## Usage

Run the graph with the default topic:

```bash
python3 agent_farm.py
```

Run the graph with your own topic:

```bash
python3 agent_farm.py --topic "European energy security in 2026"
```

Limit the number of research/review rounds:

```bash
python3 agent_farm.py --topic "Arctic geopolitics" --max-iterations 2
```

If you want to save the output into a file too:

```bash
python3 agent_farm.py --topic "AI chip competition" | tee raportti.txt
```

---

## Example Flow

```text
START
    -> Researcher
    -> Analyst
            -> PASS   -> Finalizer -> END
            -> REVISE -> Researcher -> ...
```

---

## How the code works

The main ideas are:

- `FarmState`
    Shared state that moves through the graph. It contains the topic, current report, latest analysis, verdict, score, histories, and final summary.

- `researcher_node(state)`
    Creates the first report or revises the current one using analyst feedback.

- `analyst_node(state)`
    Reviews the latest report and returns a verdict:
    - `PASS`
    - `REVISE`

- `route_after_analysis(state)`
    The routing function that decides whether the graph loops back for another revision or moves to finalization.

- `finalize_node(state)`
    Produces a short end summary once the workflow is finished.

---

## Why LangGraph Helps Here

LangGraph is useful in this version because the workflow now has:

- a shared explicit state
- conditional branching
- iterative revision rounds
- a clear graph structure instead of one long procedural function

If this were still only one research call and one analysis call, plain Python would be enough.

---

## Model fallback logic

The program tries these models in order:

1. `meta-llama/llama-3.3-70b-instruct:free`
2. `openai/gpt-oss-120b:free`
3. `google/gemma-3-27b-it:free`
4. `nvidia/nemotron-3-super-120b-a12b:free`

If a model returns HTTP `429 Too Many Requests`, the script waits and automatically tries the next model.

---

## Project structure

```text
langchain-agent-farm/
├── agent_farm.py
├── requirements.txt
├── .env
├── README.md
└── raportti.txt
```

Files:

- `agent_farm.py` - main LangGraph workflow
- `requirements.txt` - Python dependencies
- `.env` - contains your OpenRouter API key
- `README.md` - project documentation
- `raportti.txt` - optional saved output if you use `tee`

---

## Recommended .gitignore

```gitignore
.env
__pycache__/
raportti.txt
```

