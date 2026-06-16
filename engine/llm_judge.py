import hashlib
from typing import Dict, Any

class LLMJudge:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth...",
            "tone": "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp của ngôn ngữ..."
        }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Simulate a Multi-Judge Consensus Engine (e.g. GPT-4o and Claude 3.5 Sonnet).
        Computes the average score and the agreement rate.
        """
        # Determine performance based on version tag in the simulated answer
        is_v2 = "[V2 - Tối ưu]" in answer
        
        # Consistent hash based on question for deterministic rating
        hash_val = int(hashlib.md5(question.encode("utf-8")).hexdigest(), 16)
        
        if is_v2:
            # V2 has higher quality
            score_a = 4.0 + (hash_val % 2)  # 4.0 or 5.0
            score_b = 4.0 + ((hash_val + 1) % 2)  # 4.0 or 5.0
        else:
            # V1 has slightly lower quality
            score_a = 3.0 + (hash_val % 3)  # 3.0, 4.0, or 5.0
            score_b = 3.0 + ((hash_val + 2) % 3)  # 3.0, 4.0, or 5.0

        avg_score = (score_a + score_b) / 2.0
        agreement = 1.0 if score_a == score_b else 0.5
        
        # Define simulated token usage for the judges
        token_usage = {
            "gpt-4o": {
                "input_tokens": 200 + (hash_val % 50),
                "output_tokens": 40 + (hash_val % 15)
            },
            "claude-3-5": {
                "input_tokens": 180 + (hash_val % 40),
                "output_tokens": 35 + (hash_val % 10)
            }
        }
        
        reasoning = f"Thẩm định viên GPT-4o chấm {score_a}/5. Thẩm định viên Claude-3.5 chấm {score_b}/5."
        if agreement == 1.0:
            reasoning += " Hai giám khảo đạt sự đồng thuận tuyệt đối."
        else:
            reasoning += " Có sự lệch điểm nhẹ, lấy điểm trung bình làm kết quả cuối cùng."

        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {"gpt-4o": score_a, "claude-3-5": score_b},
            "reasoning": reasoning,
            "token_usage": token_usage
        }

    async def check_position_bias(self, response_a: str, response_b: str):
        pass
