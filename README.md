# Langchain Agent Farm

Built by **Jussi Niilahti**

A simple two-agent pipeline that uses free large language models via [OpenRouter](https://openrouter.ai).

- **Agent 1 (Researcher):** Generates a short factual report on a given topic
- **Agent 2 (Analyst):** Critically evaluates the report for reliability and possible bias

The agents run sequentially: the Researcher creates a report, and the Analyst evaluates that report.

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
pip3 install httpx python-dotenv
```

Packages used:

- `httpx` for HTTP requests to OpenRouter
- `python-dotenv` for loading environment variables from `.env`

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

Run the program with:

```bash
python3 agent_farm.py
```

If you want to save the terminal output into a text file at the same time:

```bash
python3 agent_farm.py | tee raportti.txt
```

This prints the output to the terminal and writes the same content into `raportti.txt`.

---

## Example output

```text
--- 🚜 SUORA AGENTTIFARMI ---
🔍 Agentti 1 tutkii...

[TUTKIJA]:
1. ...
2. ...
3. ...

------------------------------
⚖️ Agentti 2 analysoi...

[ANALYYTIKKO]:
...
```

---

## How the code works

The main parts of the code are:

- `MODELS`
    A list of free OpenRouter models. If one model is overloaded, the code tries the next one.

- `ask_model(prompt)`
    Sends a prompt to OpenRouter and returns the response text.

- `run_farm()`
    Runs the full two-agent workflow:
    - sends `researcher_prompt`
    - stores the result in `report`
    - sends `analyst_prompt`
    - stores the result in `analysis`

Workflow:

```text
researcher_prompt -> [Agent 1: Researcher] -> report
                                                                                            |
                                                                                            v
analyst_prompt + report -> [Agent 2: Analyst] -> analysis
```

The script also waits briefly between requests to reduce the chance of hitting rate limits.

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
├── .env
├── README.md
└── raportti.txt
```

Files:

- `agent_farm.py` — the main application
- `.env` — contains your OpenRouter API key
- `README.md` — project documentation
- `raportti.txt` — optional output file if you use `tee`

---

## Recommended .gitignore

```gitignore
.env
__pycache__/
raportti.txt
```

