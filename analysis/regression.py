def check_release_gate(v1_metrics: dict, v2_metrics: dict) -> tuple:
    """
    Evaluates the Auto-Gate Release vs Rollback decision.
    Calculates percentage deltas for Hit Rate, MRR, Faithfulness, Cost, and Latency.
    Checks that core quality metrics (Hit Rate, Faithfulness) don't decrease,
    and total cost doesn't increase by more than 15%.
    """
    warnings = []
    
    # Calculate percentage changes (Delta %)
    v1_hit = v1_metrics["hit_rate"]
    v2_hit = v2_metrics["hit_rate"]
    hit_rate_pct = ((v2_hit - v1_hit) / v1_hit * 100) if v1_hit > 0 else (100.0 if v2_hit > 0 else 0.0)
    
    v1_mrr = v1_metrics["mrr"]
    v2_mrr = v2_metrics["mrr"]
    mrr_pct = ((v2_mrr - v1_mrr) / v1_mrr * 100) if v1_mrr > 0 else (100.0 if v2_mrr > 0 else 0.0)
    
    v1_faith = v1_metrics["faithfulness"]
    v2_faith = v2_metrics["faithfulness"]
    faithfulness_pct = ((v2_faith - v1_faith) / v1_faith * 100) if v1_faith > 0 else (100.0 if v2_faith > 0 else 0.0)
    
    v1_cost = v1_metrics["total_cost_usd"]
    v2_cost = v2_metrics["total_cost_usd"]
    cost_pct = ((v2_cost - v1_cost) / v1_cost * 100) if v1_cost > 0 else (100.0 if v2_cost > 0 else 0.0)
    
    v1_latency = v1_metrics["avg_latency"]
    v2_latency = v2_metrics["avg_latency"]
    latency_pct = ((v2_latency - v1_latency) / v1_latency * 100) if v1_latency > 0 else (100.0 if v2_latency > 0 else 0.0)

    # Gating Checks:
    # 1. Quality metrics must not drop (delta < 0 is a rollback)
    if v2_hit < v1_hit:
        warnings.append(f"Quality check failed: Hit Rate dropped! V1: {v1_hit:.4f} -> V2: {v2_hit:.4f} (Delta: {hit_rate_pct:+.1f}%)")
    if v2_faith < v1_faith:
        warnings.append(f"Quality check failed: Faithfulness dropped! V1: {v1_faith:.4f} -> V2: {v2_faith:.4f} (Delta: {faithfulness_pct:+.1f}%)")
        
    # 2. Cost must not increase > 15%
    if cost_pct > 15.0:
        warnings.append(f"Cost limit exceeded: Cost increased by {cost_pct:+.1f}% (limit <= 15%). V1: ${v1_cost:.5f} -> V2: ${v2_cost:.5f}")
        
    decision = "ROLLBACK" if warnings else "RELEASE"
    
    deltas = {
        "hit_rate_pct": hit_rate_pct,
        "mrr_pct": mrr_pct,
        "faithfulness_pct": faithfulness_pct,
        "cost_pct": cost_pct,
        "avg_latency_pct": latency_pct
    }
    
    return decision, warnings, deltas
