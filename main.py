import asyncio
import json
import os
import time
from typing import Any, Dict, List

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner


class BenchmarkEvaluator:
    """Evaluation adapter owned by the benchmark pipeline, without changing data modules."""

    def __init__(self, top_k: int = 3):
        self.retrieval = RetrievalEvaluator()
        self.top_k = top_k

    async def score(self, case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = self._retrieved_ids(response)

        hit_rate = (
            self.retrieval.calculate_hit_rate(expected_ids, retrieved_ids, self.top_k)
            if expected_ids
            else 0.0
        )
        mrr = self.retrieval.calculate_mrr(expected_ids, retrieved_ids) if expected_ids else 0.0

        answer = response.get("answer", "")
        expected_answer = case.get("expected_answer", "")
        relevancy = self._keyword_overlap(case.get("question", ""), answer)
        faithfulness = self._keyword_overlap(expected_answer, answer)

        return {
            "faithfulness": faithfulness,
            "relevancy": relevancy,
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids,
            },
        }

    def _retrieved_ids(self, response: Dict[str, Any]) -> List[str]:
        metadata = response.get("metadata", {})
        return (
            response.get("retrieved_ids")
            or metadata.get("retrieved_ids")
            or metadata.get("sources")
            or []
        )

    def _keyword_overlap(self, expected: str, actual: str) -> float:
        expected_terms = {word.lower() for word in expected.split() if len(word) > 2}
        actual_terms = {word.lower() for word in actual.split() if len(word) > 2}
        if not expected_terms:
            return 0.0
        return round(len(expected_terms & actual_terms) / len(expected_terms), 3)


def load_dataset(path: str = "data/golden_set.jsonl") -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Missing data/golden_set.jsonl. Run '.\\venv\\Scripts\\python.exe -X utf8 data\\synthetic_gen.py' first."
        )

    with open(path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        raise ValueError("data/golden_set.jsonl is empty.")
    return dataset


async def run_benchmark_with_results(agent_version: str):
    print(f"Starting benchmark for {agent_version}...")
    dataset = load_dataset()
    start_time = time.perf_counter()

    runner = BenchmarkRunner(MainAgent(), BenchmarkEvaluator(), LLMJudge())
    results = await runner.run_all(dataset, batch_size=5)
    metrics = runner.summarize(results)
    duration_seconds = round(time.perf_counter() - start_time, 4)

    summary = {
        "metadata": {
            "version": agent_version,
            "total": len(results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration_seconds,
            "batch_size": 5,
        },
        "metrics": metrics,
    }
    return results, summary


async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary


async def main():
    try:
        v1_summary = await run_benchmark("Agent_V1_Base")
        v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Cannot run benchmark: {exc}")
        return

    print("\n--- REGRESSION COMPARISON ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")
    print(f"Agreement Rate: {v2_summary['metrics']['agreement_rate']}")
    print(f"Avg Latency: {v2_summary['metrics']['avg_latency']}s")
    print(f"Total Cost Estimate: ${v2_summary['metrics']['total_cost_usd']}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta > 0:
        print("RELEASE DECISION: APPROVE")
    else:
        print("RELEASE DECISION: BLOCK RELEASE")


if __name__ == "__main__":
    asyncio.run(main())
