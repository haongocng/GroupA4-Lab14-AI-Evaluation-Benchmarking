# Reflection - Nguyen Ngoc Hao

## Vai tro
Hao phu trach phan AI Core cua benchmark pipeline: async runner, multi-judge consensus, va ket noi engine vao `main.py`.

## Buoc 1 - Multi-Judge Consensus
- File thuc hien: `engine/llm_judge.py`
- Ket qua: cai dat `LLMJudge` gom 2 judge mo phong doc lap:
  - `gpt-4o-mini-sim`: cham accuracy dua tren muc do phu khop voi ground truth.
  - `claude-3-haiku-sim`: cham faithfulness/safety dua tren muc do grounded va dau hieu cau tra loi mau.
- Logic consensus:
  - Tinh diem trung binh neu 2 judge dong thuan du nguong.
  - Tinh `agreement_rate = 1 - max_delta / 4`.
  - Neu diem lech lon hon `conflict_threshold`, kich hoat `tie-breaker-sim` va lay conservative average.
- Nhan xet: cach nay giup bai lab co bang chung ro rang rang he thong khong phu thuoc vao mot judge duy nhat.

## Buoc 2 - Async Benchmark Runner
- File thuc hien: `engine/runner.py`
- Ket qua: nang cap `BenchmarkRunner` de chay tung batch bang `asyncio.gather`.
- Cac chi so duoc ghi lai:
  - `latency`
  - `tokens_used`
  - `cost_estimate_usd`
  - `status`
  - `agreement_rate`
  - `conflict_rate`
- Xu ly loi: neu mot test case loi, runner tra ve status `error` cho case do thay vi lam sap toan bo benchmark.
- Nhan xet: day la phan chung minh tieu chi Performance Async va Engineering Contribution cua Hao.

## Buoc 3 - Ket noi vao main.py
- File thuc hien: `main.py`
- Ket qua:
  - Thay judge gia lap trong `main.py` bang `LLMJudge`.
  - Thay cach tinh summary thu cong bang `runner.summarize`.
  - Ghi them `duration_seconds`, `batch_size`, `avg_latency`, `total_tokens`, va `total_cost_usd`.
- Nhan xet: `main.py` chi dong vai tro orchestration; logic AI phuc tap nam trong `engine/` de giam conflict voi phan cua thanh vien khac.

## Kiem thu
```powershell
.\venv\Scripts\python.exe -X utf8 data\synthetic_gen.py
.\venv\Scripts\python.exe -X utf8 main.py
.\venv\Scripts\python.exe -X utf8 check_lab.py
```

Ket qua thuc te sau khi chay trong venv:
- `py_compile` cho `main.py`, `engine/runner.py`, `engine/llm_judge.py`: pass.
- `data/synthetic_gen.py`: tao duoc `data/golden_set.jsonl`.
- `main.py`: tao duoc `reports/summary.json` va `reports/benchmark_results.json`.
- `check_lab.py`: pass dinh dang nop bai.

Chi so benchmark hien tai:
- Tong so cases: 1
- Avg score: 1.12
- Hit rate: 0.0
- MRR: 0.0
- Agreement rate: 0.94
- Pass rate: 0.0
- Conflict rate: 0.0
- Avg latency: 0.5159s
- Total tokens: 150
- Total cost estimate: 0.000022 USD

Nhan xet ket qua:
- Diem thap khong phai do runner hay consensus bi loi, ma do repo hien tai van la skeleton.
- `data/synthetic_gen.py` moi sinh 1 case, chua du yeu cau 50+ cases.
- Golden dataset chua co `expected_retrieval_ids`, nen Hit Rate va MRR bang 0.
- `agent/main_agent.py` van tra loi mau, nen judge cham accuracy/faithfulness thap.
- Phan cua Hao da san sang nhan dataset that va agent that tu cac thanh vien khac de benchmark lai.

## Giai trinh ky thuat
- Async: dung `asyncio.gather` theo batch de chay nhieu case cung luc, tranh benchmark tuan tu qua cham.
- Timeout/rate limit: trong ban hien tai runner da co khung bat loi tung case; neu dung API that, co the them retry va timeout quanh tung judge call.
- Cohen's Kappa: la metric do muc do dong thuan giua cac judge sau khi tru di phan dong thuan do ngau nhien. Trong ban lab nay, `agreement_rate` la metric don gian hon, nhung cung phuc vu muc tieu quan sat do on dinh giua judge.
- Position Bias: judge co the thien vi cau tra loi xuat hien truoc. File `LLMJudge` co ham `check_position_bias` de swap thu tu response va do delta.
- Cost vs Quality: them nhieu judge lam ket qua dang tin hon nhung tang chi phi. Vi vay he thong chi goi tie-breaker khi 2 judge lech qua nguong.
