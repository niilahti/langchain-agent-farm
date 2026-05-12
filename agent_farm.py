import argparse
import os
import re
import time
from typing import Any, Dict, List, Literal, TypedDict

import httpx
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

# Load environment variables from .env so the API key is available locally.
load_dotenv(override=True)
api_key = os.getenv("OPENROUTER_API_KEY")

# Free OpenRouter models to try in order. If one is rate-limited, the code
# automatically falls back to the next model.
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]


class FarmState(TypedDict):
    """Shared state that moves through the LangGraph workflow."""

    topic: str
    max_iterations: int
    iteration: int
    report: str
    analysis: str
    feedback: str
    verdict: Literal["PASS", "REVISE"]
    score: int
    report_history: List[str]
    analysis_history: List[str]
    final_summary: str


def ask_model(prompt: str) -> str:
    """Send a prompt to OpenRouter and return the model's text response."""
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY puuttuu .env-tiedostosta.")

    for model in MODELS:
        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 429:
                print(f"  (malli {model} ylikuormittunut, odotetaan 10s...)")
                time.sleep(10)
                continue
            raise

    raise RuntimeError("Kaikki mallit ylikuormittuneita, yritä myöhemmin uudelleen.")


def build_research_prompt(state: FarmState) -> str:
    """Create the prompt for the researcher node.

    The first iteration produces an initial report. Later iterations use the
    analyst's feedback to revise the report instead of starting from scratch.
    """
    if state["iteration"] == 0:
        return (
            "Olet OSINT-tutkija. Kirjoita aiheesta lyhyt raportti, jossa on 3 "
            "selkeaa havaintoa. Kerro vain todennakoisina pitamasi asiat, valta "
            "liioittelua ja tuo esiin epavarmuus, jos tieto voi olla vanhentunutta.\n\n"
            f"Aihe: {state['topic']}"
        )

    return (
        "Olet OSINT-tutkija. Korjaa aiempaa raporttia analyytikon palautteen "
        "perusteella. Pida raportti ytimekkaana, mutta korjaa epatarkkuudet, "
        "epaselvyydet ja mahdolliset vinoumat.\n\n"
        f"Aihe: {state['topic']}\n\n"
        f"Aiempi raportti:\n{state['report']}\n\n"
        f"Analyytikon palaute:\n{state['feedback']}"
    )


def build_analyst_prompt(report: str) -> str:
    """Ask the analyst to evaluate the report in a predictable text format."""
    return (
        "Olet kriittinen analyytikko. Arvioi alla olevan raportin luotettavuus, "
        "selkeys ja mahdolliset vinoumat. Vastaa TASMALLEEN tassa muodossa:\n\n"
        "VERDICT: PASS tai REVISE\n"
        "SCORE: kokonaisluku valilta 1-10\n"
        "FEEDBACK: 2-4 lyhytta virkettä, joissa kerrot mita pitäisi korjata tai "
        "miksi raportti on riittavan hyva.\n\n"
        f"Raportti:\n{report}"
    )


def build_summary_prompt(state: FarmState) -> str:
    """Create the final summarizer prompt from the latest graph state."""
    return (
        "Laadi lopuksi lyhyt yhteenveto tasta agenttikierroksesta. Kerro lyhyesti "
        "lopullinen raportti, analyytikon viimeinen arvio ja montako kierrosta "
        "tarvittiin.\n\n"
        f"Aihe: {state['topic']}\n"
        f"Kierroksia: {state['iteration'] + 1}\n\n"
        f"Lopullinen raportti:\n{state['report']}\n\n"
        f"Viimeinen analyysi:\n{state['analysis']}"
    )


def parse_analyst_response(text: str) -> Dict[str, Any]:
    """Extract verdict, score and feedback from the analyst response.

    Free models are not perfectly reliable, so the parser falls back to safe
    defaults if the response format is imperfect.
    """
    verdict_match = re.search(r"VERDICT:\s*(PASS|REVISE)", text)
    score_match = re.search(r"SCORE:\s*(\d+)", text)
    feedback_match = re.search(r"FEEDBACK:\s*(.*)", text, re.DOTALL)

    verdict: Literal["PASS", "REVISE"] = "REVISE"
    if verdict_match:
        verdict = verdict_match.group(1)

    score = 0
    if score_match:
        score = max(0, min(10, int(score_match.group(1))))

    feedback = text.strip()
    if feedback_match:
        feedback = feedback_match.group(1).strip()

    return {"verdict": verdict, "score": score, "feedback": feedback}


def researcher_node(state: FarmState) -> Dict[str, Any]:
    """Generate or revise the report based on the current graph state."""
    current_round = state["iteration"] + 1
    print(f"\n🔍 Tutkija, kierros {current_round}...")

    report = ask_model(build_research_prompt(state))
    print(f"\n[TUTKIJA / {current_round}]:\n{report}\n")

    return {
        "report": report,
        "report_history": state["report_history"] + [report],
    }


def analyst_node(state: FarmState) -> Dict[str, Any]:
    """Evaluate the latest report and decide whether another revision is needed."""
    current_round = state["iteration"] + 1
    print("-" * 30)
    print(f"⚖️ Analyytikko, kierros {current_round}...")

    analysis = ask_model(build_analyst_prompt(state["report"]))
    parsed = parse_analyst_response(analysis)

    print(f"\n[ANALYYTIKKO / {current_round}]:\n{analysis}\n")

    return {
        "analysis": analysis,
        "feedback": parsed["feedback"],
        "verdict": parsed["verdict"],
        "score": parsed["score"],
        "analysis_history": state["analysis_history"] + [analysis],
    }


def finalize_node(state: FarmState) -> Dict[str, Any]:
    """Produce a short final summary after the graph has finished iterating."""
    print("-" * 30)
    print("🧾 Luodaan lopullinen yhteenveto...")

    final_summary = ask_model(build_summary_prompt(state))
    print(f"\n[YHTEENVETO]:\n{final_summary}\n")

    return {"final_summary": final_summary}


def route_after_analysis(state: FarmState) -> str:
    """Choose whether to loop back for revision or finish the workflow.

    The graph continues only when the analyst explicitly requests revision and
    the maximum number of rounds has not been reached.
    """
    reached_limit = state["iteration"] + 1 >= state["max_iterations"]
    needs_revision = state["verdict"] == "REVISE"

    if needs_revision and not reached_limit:
        print("↩️ Analyytikko pyysi korjauksia, tehdään uusi tutkimuskierros.")
        return "revise"

    print("✅ Tyonkulku voi paattya nykyiseen versioon.")
    return "finish"


def increment_iteration(state: FarmState) -> Dict[str, int]:
    """Advance the loop counter before returning to the researcher node."""
    return {"iteration": state["iteration"] + 1}


def build_graph() -> Any:
    """Assemble the LangGraph state machine for the agent workflow."""
    graph = StateGraph(FarmState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("increment_iteration", increment_iteration)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_conditional_edges(
        "analyst",
        route_after_analysis,
        {
            "revise": "increment_iteration",
            "finish": "finalize",
        },
    )
    graph.add_edge("increment_iteration", "researcher")
    graph.add_edge("finalize", END)
    return graph.compile()


def parse_args() -> argparse.Namespace:
    """Read the topic and iteration limit from the command line."""
    parser = argparse.ArgumentParser(description="LangGraph Agent Farm")
    parser.add_argument(
        "--topic",
        default="Ukrainan sodan tilanne tanaan",
        help="Aihe, josta tutkija laatii raportin.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maksimimaara tutkimus/analyysi-kierroksia.",
    )
    return parser.parse_args()


def run_farm(topic: str, max_iterations: int) -> FarmState:
    """Run the LangGraph workflow from the initial state to the final summary."""
    print("--- 🚜 LANGGRAPH AGENT FARM ---")

    app = build_graph()
    initial_state: FarmState = {
        "topic": topic,
        "max_iterations": max(1, max_iterations),
        "iteration": 0,
        "report": "",
        "analysis": "",
        "feedback": "",
        "verdict": "REVISE",
        "score": 0,
        "report_history": [],
        "analysis_history": [],
        "final_summary": "",
    }

    return app.invoke(initial_state)


if __name__ == "__main__":
    arguments = parse_args()

    try:
        run_farm(arguments.topic, arguments.max_iterations)
    except Exception as error:
        print(f"\n❌ VIRHE: {error}")
