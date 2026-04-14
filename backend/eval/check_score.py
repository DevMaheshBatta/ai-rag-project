import json
import sys

with open("backend/eval/results.json") as f:
    data = json.load(f)

score = data["faithfulness"]

THRESHOLD = 0.7

if score < THRESHOLD:
    print("❌ CI FAILED: Score too low")
    sys.exit(1)
else:
    print("✅ CI PASSED")