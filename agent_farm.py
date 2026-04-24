import os
import time
import httpx
from dotenv import load_dotenv

# ladataan avain
load_dotenv(override=True)
api_key = os.getenv("OPENROUTER_API_KEY")

MALLIT = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

def kysy(prompt):
    for malli in MALLIT:
        try:
            r = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": malli, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048},
                timeout=30
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"  (malli {malli} ylikuormittunut, odotetaan 10s...)")
                time.sleep(10)
                continue
            raise
    raise RuntimeError("Kaikki mallit ylikuormittuneita, yritä myöhemmin uudelleen.")

def aja_farmi():
    print("--- SUORA AGENTTIFARMI ---")
    
    try:
        # AGENTTI 1: TUTKIJA
        print(" Agentti 1 tutkii...")
        prompt1 = "Olet OSINT-tutkija. Listaa 3 lyhyttä faktaa Ukrainan sodan tilanteesta tänään."
        raportti = kysy(prompt1)
        print(f"\n[TUTKIJA]:\n{raportti}\n")

        print("-" * 30)
        time.sleep(5)

        # AGENTTI 2: ANALYYTIKKO
        print("⚖️ Agentti 2 analysoi...")
        prompt2 = f"Olet kriittinen analyytikko. Arvioi tämän raportin luotettavuus ja mahdolliset vinoumat: {raportti}"
        analyysi = kysy(prompt2)
        print(f"\n[ANALYYTIKKO]:\n{analyysi}")

    except Exception as e:
        print(f"\n❌ VIRHE: {e}")

if __name__ == "__main__":
    aja_farmi()