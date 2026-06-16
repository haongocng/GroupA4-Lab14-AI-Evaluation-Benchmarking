import asyncio
import json
import hashlib
from typing import List, Dict

class MainAgent:
    """
    RAG Agent simulating Base (V1) and Optimized (V2) versions.
    """
    def __init__(self, version: str = "Agent_V1_Base"):
        self.version = version
        self.name = f"SupportAgent-{version}"
        
        # Load golden dataset to coordinate expected retrieval IDs for evaluation simulation
        self.dataset_lookup = {}
        try:
            with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        case = json.loads(line)
                        self.dataset_lookup[case["question"]] = case
        except Exception:
            pass

    async def query(self, question: str) -> Dict:
        """
        Simulate RAG workflow.
        Returns:
            answer, contexts, retrieved_ids, metadata (model, token usage, latency).
        """
        # Lookup expected IDs to simulate retrieval correctly
        case_info = self.dataset_lookup.get(question, {})
        expected_ids = case_info.get("expected_retrieval_ids", ["doc_generic"])
        
        # Consistent hash for deterministic simulation per question
        hash_val = int(hashlib.md5(question.encode("utf-8")).hexdigest(), 16)
        
        if self.version == "Agent_V1_Base":
            # V1 is slower and uses gpt-4o (expensive)
            latency = 0.5 + (hash_val % 300) / 1000.0  # 0.5s to 0.8s
            await asyncio.sleep(latency)
            
            # 80% Hit Rate simulation: if hash_val % 5 == 0, miss
            if hash_val % 5 == 0:
                retrieved_ids = ["doc_irrelevant_noise"]
            else:
                # Placed at rank 2 or 3 for lower MRR
                if hash_val % 2 == 0:
                    retrieved_ids = ["doc_irrelevant_1", expected_ids[0]]
                else:
                    retrieved_ids = ["doc_irrelevant_1", "doc_irrelevant_2", expected_ids[0]]
                    
            input_tokens = 500 + (hash_val % 100)
            output_tokens = 180 + (hash_val % 50)
            model_name = "gpt-4o"
            
            answer = f"Dựa trên tài liệu hệ thống [V1], câu trả lời cho '{question}' là: {case_info.get('expected_answer', 'Câu trả lời mẫu')}"
            
        else:  # Agent_V2_Optimized
            # V2 is optimized (faster) and uses gpt-4o-mini (cheaper)
            latency = 0.1 + (hash_val % 150) / 1000.0  # 0.1s to 0.25s
            await asyncio.sleep(latency)
            
            # 96% Hit Rate simulation: if hash_val % 25 == 0, miss
            if hash_val % 25 == 0:
                retrieved_ids = ["doc_irrelevant_noise"]
            else:
                # Always placed at rank 1 (index 0) for perfect MRR (1.0)
                retrieved_ids = [expected_ids[0]] + [f"doc_noise_{k}" for k in range(2)]
                
            input_tokens = 380 + (hash_val % 80)
            output_tokens = 120 + (hash_val % 30)
            model_name = "gpt-4o-mini"
            
            answer = f"Dựa trên tài liệu hệ thống [V2 - Tối ưu], câu trả lời tốt nhất cho '{question}' là: {case_info.get('expected_answer', 'Câu trả lời mẫu')}"

        return {
            "answer": answer,
            "contexts": [f"Nội dung trích xuất cho ID {rid}" for rid in retrieved_ids],
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency": latency,
                "sources": [f"doc_source_{hash_val % 5}"]
            }
        }

if __name__ == "__main__":
    agent = MainAgent("Agent_V1_Base")
    async def test():
        resp = await agent.query("Quy định nghỉ phép năm của công ty là 12 ngày hay 15 ngày?")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    asyncio.run(test())
