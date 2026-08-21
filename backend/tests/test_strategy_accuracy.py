import os
import csv
import pytest
from app.services.rag_service import _fallback_keyword_strategy_match

@pytest.mark.asyncio
async def test_strategy_classification_benchmark():
    csv_path = os.path.join(os.path.dirname(__file__), "strategy_eval.csv")
    assert os.path.exists(csv_path), "Golden dataset strategy_eval.csv not found in tests/"

    valid_samples = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gold = row.get("gold_strategy", "").strip()
            msg = row.get("message", "").strip()
            if gold and gold.lower() != "nan" and msg:
                valid_samples.append((msg, gold))

    assert len(valid_samples) > 0, "No valid strategy evaluation samples found in CSV"

    correct = 0
    total = 0

    for msg, gold in valid_samples[:100]:  # Evaluate top 100 annotated samples
        total += 1
        predictions = _fallback_keyword_strategy_match(msg)
        pred_code = predictions[0]["strategy_id"] if predictions else "000-000"

        # Check exact or category match
        if pred_code == gold or pred_code.split("-")[0] == gold.split("-")[0]:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    print(f"\n[Benchmark] Tested {total} golden samples. Category Accuracy: {accuracy * 100:.2f}%")
    assert total > 0
