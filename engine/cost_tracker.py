from typing import Dict, Any

# Price per token in USD (Standard Pricing Table)
MODEL_PRICING = {
    "gpt-4o": {
        "input": 5.00 / 1_000_000,
        "output": 15.00 / 1_000_000
    },
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000
    },
    "gpt-4o-mini-sim": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000
    },
    "claude-3-haiku-sim": {
        "input": 0.25 / 1_000_000,
        "output": 1.25 / 1_000_000
    },
    "tie-breaker-sim": {
        "input": 5.00 / 1_000_000,
        "output": 15.00 / 1_000_000
    },
    "claude-3-5-sonnet": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000
    },
    "claude-3-5": {  # Alias for claude-3-5-sonnet
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000
    }
}

def calculate_token_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculates cost of LLM call in USD.
    """
    model_name = model_name.lower().strip()
    
    # Simple fallback: if model is not defined, use gpt-4o-mini prices
    pricing = MODEL_PRICING.get(model_name, MODEL_PRICING["gpt-4o-mini"])
    
    cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
    return cost

def get_detailed_cost(usage_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates costs and updates the token usage metadata dictionary.
    Assumes structure like:
    {
      "agent": {"model": "...", "input_tokens": x, "output_tokens": y},
      "evaluator": {"model": "...", "input_tokens": x, "output_tokens": y},
      "judge": {
         "model1": {"input_tokens": x, "output_tokens": y},
         ...
      }
    }
    """
    total_tokens = 0
    total_cost = 0.0
    
    result = {}
    
    # Calculate for agent
    if "agent" in usage_dict:
        agent_data = usage_dict["agent"]
        m = agent_data.get("model", "gpt-4o-mini")
        i = agent_data.get("input_tokens", 0)
        o = agent_data.get("output_tokens", 0)
        cost = calculate_token_cost(m, i, o)
        total_tokens += (i + o)
        total_cost += cost
        result["agent"] = {
            "model": m,
            "input_tokens": i,
            "output_tokens": o,
            "cost_usd": cost
        }
        
    # Calculate for evaluator
    if "evaluator" in usage_dict:
        eval_data = usage_dict["evaluator"]
        m = eval_data.get("model", "gpt-4o-mini")
        i = eval_data.get("input_tokens", 0)
        o = eval_data.get("output_tokens", 0)
        cost = calculate_token_cost(m, i, o)
        total_tokens += (i + o)
        total_cost += cost
        result["evaluator"] = {
            "model": m,
            "input_tokens": i,
            "output_tokens": o,
            "cost_usd": cost
        }
        
    # Calculate for judge (can have multiple models)
    if "judge" in usage_dict:
        judge_data = usage_dict["judge"]
        result["judge"] = {}
        for m, m_data in judge_data.items():
            i = m_data.get("input_tokens", 0)
            o = m_data.get("output_tokens", 0)
            cost = calculate_token_cost(m, i, o)
            total_tokens += (i + o)
            total_cost += cost
            result["judge"][m] = {
                "input_tokens": i,
                "output_tokens": o,
                "cost_usd": cost
            }
            
    result["total_tokens"] = total_tokens
    result["total_cost_usd"] = total_cost
    return result
