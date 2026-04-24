# Langchain Agent Farm

A simple two-agent pipeline that uses free large language models via [OpenRouter](https://openrouter.ai):

- **Agent 1 (Researcher):** Generates a short factual report on a given topic
- **Agent 2 (Analyst):** Critically evaluates the report for reliability and potential bias

The agents communicate sequentially — the researcher's output is passed directly as input to the analyst.

---

## Requirements

- Python 3.9+
- An OpenRouter API key (free tier, no credit card required)

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

| Package        | Purpose                                      |
|----------------|----------------------------------------------|
| `httpx`        | HTTP client for calling the OpenRouter API   |
| `python-dotenv`| Loads the API key from the `.env` file       |

---

## Configuration

### 1. Get an OpenRouter API key

1. Go to [openrouter.ai](https://openrouter.ai) and create a free account
2. Navigate to **Keys** → [openrouter.ai/keys](https://openrouter.ai/keys)
3. Click **Create key**
4. Copy the key — it starts with `sk-or-v1-`

> The free tier gives access to many large models (Llama 3.3 70B, GPT-OSS 120B, Gemma 3 27B etc.) without requiring payment details.

### 2. Create the `.env` file

Create a file named `.env` in the project root:

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **Important:** Do not add quotes around the key. Do not add spaces around `=`.

The `.env` file is intentionally excluded from version control — never commit it to Git.

---

## Usage

```bash
python3 agent_farm.py
```

### Example output

```
--- 🚜 SUORA AGENTTIFARMI ---
🔍 Agentti 1 tutkii...

[TUTKIJA]:
1. Venäjän joukot ovat jatkaneet hyökkäyksiä Harkovan alueella...
2. Ukraina on saanut lisää ilmatorjuntaohjuksia länsimailta...
3. YK on raportoinut kasvavista siviiliuhreista Donbassin alueella...

------------------------------
⚖️ Agentti 2 analysoi...

[ANALYYTIKKO]:
Raportin luotettavuusarviointi:
1. Harkovan hyökkäykset — tieto on uskottava, mutta...
```

---

## How it works

```
prompt1 → [Agent 1: Researcher] → report
                                      ↓
                         prompt2 + report → [Agent 2: Analyst] → analysis
```

The code automatically tries multiple free models in order if one is rate-limited (429). Models are tried in this order:

1. `meta-llama/llama-3.3-70b-instruct:free`
2. `openai/gpt-oss-120b:free`
3. `google/gemma-3-27b-it:free`
4. `nvidia/nemotron-3-super-120b-a12b:free`

---

## Project structure

```
langchain-agent-farm/
├── agent_farm.py   # Main application
├── .env            # API key (not committed to Git)
├── .gitignore      # Should include .env
└── README.md       # This file
```

---

## .gitignore recommendation

Make sure your `.gitignore` contains at least:

```
.env
__pycache__/
```

