# Two things to add to your FastAPI backend

## 1. Add /eval/latest endpoint to app/main.py

Add this import at the top:

    import json
    from pathlib import Path

Add this route (after the /health route):

    @app.get("/eval/latest", tags=["Evaluation"])
    def eval_latest():
        p = Path("eval/results/latest.json")
        if not p.exists():
            raise HTTPException(404, "No eval results yet. Run: python eval/run_ragas_eval.py")
        return json.loads(p.read_text())

That's it. Your run_ragas_eval.py already writes eval/results/latest.json,
so this endpoint just serves that file.


## 2. /documents endpoint must return this shape

Your app/routers/documents.py GET /documents must return a list like:

    [
      {
        "id": "some-unique-id",
        "filename": "paper.pdf",
        "pages": 12,
        "chunks": 48,
        "uploaded_at": "2024-01-15T10:30:00"
      }
    ]

The frontend handles both a raw array OR { "documents": [...] }.
