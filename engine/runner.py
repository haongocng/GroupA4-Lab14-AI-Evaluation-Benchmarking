import asyncio
import time
from typing import Any, Dict, List
from engine.cost_tracker import get_detailed_cost

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
        
        # Support both Hang's and Hao's schemas
        q = test_case.get("query") or test_case.get("question") or ""
        gt = test_case.get("ground_truth_answer") or test_case.get("expected_answer") or ""
        case_id = test_case.get("id") or test_case.get("case_id") or q
        
        try:
            # 1. Query the Agent
            response = await self.agent.query(q)
            latency = time.perf_counter() - start_time
            
            # 2. Run RAGAS / Retrieval metrics
            ragas_scores = await self.evaluator.score(test_case, response)
            
            # 3. Run Multi-Judge
            judge_result = await self.judge.evaluate_multi_judge(
                q,
                response.get("answer", ""),
                gt
            )
            
            # 4. Detailed Token Usage & Cost (Lam's DevOps Contribution)
            agent_meta = response.get("metadata", {})
            usage_dict = {
                "agent": {
                    "model": agent_meta.get("model", "gpt-4o-mini"),
                    "input_tokens": agent_meta.get("input_tokens", 0),
                    "output_tokens": agent_meta.get("output_tokens", 0)
                },
                "evaluator": ragas_scores.get("token_usage", {
                    "model": "gpt-4o-mini",
                    "input_tokens": 150,
                    "output_tokens": 30
                }),
                "judge": judge_result.get("token_usage", {
                    "gpt-4o-mini-sim": {"input_tokens": 200, "output_tokens": 40},
                    "claude-3-haiku-sim": {"input_tokens": 180, "output_tokens": 35}
                })
            }
            
            token_usage_details = get_detailed_cost(usage_dict)
            status = "pass" if judge_result["final_score"] >= self.pass_threshold else "fail"
            
            return {
                "id": case_id,
                "test_case": q,
                "agent_response": response.get("answer", ""),
                "contexts": response.get("contexts", []),
                "latency": round(latency, 4),
                "tokens_used": token_usage_details["total_tokens"],
                "cost_estimate_usd": token_usage_details["total_cost_usd"],
                "token_usage": token_usage_details,
                "ragas": {
                    "faithfulness": ragas_scores.get("faithfulness", 0.0),
                    "relevancy": ragas_scores.get("relevancy", 0.0),
                    "retrieval": ragas_scores.get("retrieval", {"hit_rate": 0.0, "mrr": 0.0})
                },
                "judge": judge_result,
                "status": status,
                "error": None
            }
        except Exception as exc:
            latency = time.perf_counter() - start_time
            return {
                "id": case_id,
                "test_case": q,
                "agent_response": "",
                "contexts": [],
                "latency": round(latency, 4),
                "tokens_used": 0,
                "cost_estimate_usd": 0.0,
                "token_usage": {},
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

    async def run_all(self, dataset: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
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
                "faithfulness": 0.0,
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
            "faithfulness": round(sum(r["ragas"]["faithfulness"] for r in results) / total, 3),
            "agreement_rate": round(sum(r["judge"]["agreement_rate"] for r in results) / total, 3),
            "pass_rate": round(sum(1 for r in results if r["status"] == "pass") / total, 3),
            "conflict_rate": round(sum(1 for r in results if r["judge"].get("conflict")) / total, 3),
            "avg_latency": round(sum(r["latency"] for r in results) / total, 4),
            "total_tokens": sum(r["tokens_used"] for r in results),
            "total_cost_usd": round(sum(r["cost_estimate_usd"] for r in results), 6),
        }
