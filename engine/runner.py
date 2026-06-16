import asyncio
import time
from typing import Any, Dict, List


class BenchmarkRunner:
    def __init__(
        self,
        agent,
        evaluator,
        judge,
        pass_threshold: float = 3.0,
        cost_per_1k_tokens: float = 0.00015,
    ):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.pass_threshold = pass_threshold
        self.cost_per_1k_tokens = cost_per_1k_tokens

    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        case_id = test_case.get("id") or test_case.get("case_id") or test_case.get("question")

        try:
            response = await self.agent.query(test_case["question"])
            ragas_scores = await self.evaluator.score(test_case, response)
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"],
                response.get("answer", ""),
                test_case.get("expected_answer", ""),
            )

            latency = time.perf_counter() - start_time
            tokens_used = self._extract_tokens(response)
            cost_estimate = self._estimate_cost(tokens_used)
            status = "pass" if judge_result["final_score"] >= self.pass_threshold else "fail"

            return {
                "id": case_id,
                "test_case": test_case["question"],
                "agent_response": response.get("answer", ""),
                "contexts": response.get("contexts", []),
                "latency": round(latency, 4),
                "tokens_used": tokens_used,
                "cost_estimate_usd": cost_estimate,
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": status,
                "error": None,
            }
        except Exception as exc:
            latency = time.perf_counter() - start_time
            return {
                "id": case_id,
                "test_case": test_case.get("question", ""),
                "agent_response": "",
                "contexts": [],
                "latency": round(latency, 4),
                "tokens_used": 0,
                "cost_estimate_usd": 0.0,
                "ragas": {"faithfulness": 0.0, "relevancy": 0.0, "retrieval": {"hit_rate": 0.0, "mrr": 0.0}},
                "judge": {
                    "final_score": 1.0,
                    "agreement_rate": 0.0,
                    "conflict": True,
                    "individual_scores": {},
                    "reasoning": f"Evaluation failed: {exc}",
                },
                "status": "error",
                "error": str(exc),
            }

    async def run_all(self, dataset: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        total = len(results)
        if total == 0:
            return {
                "avg_score": 0.0,
                "hit_rate": 0.0,
                "mrr": 0.0,
                "agreement_rate": 0.0,
                "pass_rate": 0.0,
                "conflict_rate": 0.0,
                "avg_latency": 0.0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }

        return {
            "avg_score": round(sum(r["judge"]["final_score"] for r in results) / total, 3),
            "hit_rate": round(sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total, 3),
            "mrr": round(sum(r["ragas"]["retrieval"]["mrr"] for r in results) / total, 3),
            "agreement_rate": round(sum(r["judge"]["agreement_rate"] for r in results) / total, 3),
            "pass_rate": round(sum(1 for r in results if r["status"] == "pass") / total, 3),
            "conflict_rate": round(sum(1 for r in results if r["judge"].get("conflict")) / total, 3),
            "avg_latency": round(sum(r["latency"] for r in results) / total, 4),
            "total_tokens": sum(r["tokens_used"] for r in results),
            "total_cost_usd": round(sum(r["cost_estimate_usd"] for r in results), 6),
        }

    def _extract_tokens(self, response: Dict[str, Any]) -> int:
        metadata = response.get("metadata", {})
        return int(metadata.get("tokens_used", 0) or 0)

    def _estimate_cost(self, tokens_used: int) -> float:
        return round((tokens_used / 1000) * self.cost_per_1k_tokens, 6)
