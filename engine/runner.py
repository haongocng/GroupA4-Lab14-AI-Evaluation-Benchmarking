import asyncio
import time
from typing import List, Dict
from engine.cost_tracker import get_detailed_cost

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        
        # Determine keys for both schemas
        q = test_case.get("query") or test_case.get("question")
        gt = test_case.get("ground_truth_answer") or test_case.get("expected_answer")
        
        # 1. Query the Agent
        response = await self.agent.query(q)
        latency = time.perf_counter() - start_time
        
        # 2. Run RAGAS / Retrieval metrics
        ragas_scores = await self.evaluator.score(test_case, response)
        
        # 3. Run Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            q, 
            response["answer"], 
            gt
        )
        
        # 4. Track Token Usage & Cost
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
                "gpt-4o": {"input_tokens": 200, "output_tokens": 40},
                "claude-3-5": {"input_tokens": 180, "output_tokens": 35}
            })
        }
        
        token_usage_details = get_detailed_cost(usage_dict)
        
        # Add latency inside the runner response
        return {
            "test_case": q,
            "agent_response": response["answer"],
            "latency": latency,
            "ragas": {
                "faithfulness": ragas_scores.get("faithfulness", 0.0),
                "relevancy": ragas_scores.get("relevancy", 0.0),
                "retrieval": ragas_scores.get("retrieval", {"hit_rate": 0.0, "mrr": 0.0})
            },
            "judge": {
                "final_score": judge_result["final_score"],
                "agreement_rate": judge_result["agreement_rate"],
                "individual_scores": judge_result.get("individual_scores", {}),
                "reasoning": judge_result.get("reasoning", "")
            },
            "token_usage": token_usage_details,
            "status": "fail" if judge_result["final_score"] < 3 else "pass"
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 10) -> List[Dict]:
        """
        Run test cases concurrently with a batch limit to prevent rate limits.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
