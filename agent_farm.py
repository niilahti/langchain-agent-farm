import os
import time
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file, overriding any existing shell variables
load_dotenv(override=True)
api_key = os.getenv("OPENROUTER_API_KEY")

# List of free models to try in order. If the first model is rate-limited (429),
# the code automatically falls back to the next one.
# Only large models (27B–120B parameters) are included to ensure coherent output quality.
MALLIT = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

def kysy(prompt):
    """Send a prompt to OpenRouter and return the model's text response.
    
    Iterates through the MALLIT list and retries with the next model if a 429
    rate-limit error is encountered. Raises RuntimeError if all models are exhausted.
    """
    for malli in MALLIT:
        try:
            # POST request to OpenRouter's OpenAI-compatible chat completions endpoint
            r = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": malli, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048},
                timeout=30
            )
            r.raise_for_status()
            # Extract the assistant's reply from the response JSON
            return r.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Model is overloaded — wait briefly and try the next one
                print(f"  (malli {malli} ylikuormittunut, odotetaan 10s...)")
                time.sleep(10)
                continue
            raise
    raise RuntimeError("Kaikki mallit ylikuormittuneita, yritä myöhemmin uudelleen.")

def aja_farmi():
    """Run the two-agent pipeline:
    
    Agent 1 (Researcher): Generates a short factual report on a given topic.
    Agent 2 (Analyst):    Critically evaluates the report for reliability and bias.
    A 5-second pause between agents avoids hitting per-minute rate limits.
    """
    print("--- 🚜 SUORA AGENTTIFARMI ---")
    
    try:
        # AGENT 1: RESEARCHER — produces a short factual report
        print("🔍 Agentti 1 tutkii...")
        prompt1 = "Olet OSINT-tutkija. Listaa 3 lyhyttä faktaa Ukrainan sodan tilanteesta tänään."
        raportti = kysy(prompt1)
        print(f"\n[TUTKIJA]:\n{raportti}\n")

        print("-" * 30)
        # Pause between requests to stay within free-tier rate limits
        time.sleep(5)

        # AGENT 2: ANALYST — evaluates the researcher's report for bias and reliability
        print("⚖️ Agentti 2 analysoi...")
        prompt2 = f"Olet kriittinen analyytikko. Arvioi tämän raportin luotettavuus ja mahdolliset vinoumat: {raportti}"
        analyysi = kysy(prompt2)
        print(f"\n[ANALYYTIKKO]:\n{analyysi}")

    except Exception as e:
        print(f"\n❌ VIRHE: {e}")

# Entry point — only runs when executed directly, not when imported as a module
if __name__ == "__main__":
    aja_farmi()
