"""
RAG Accuracy Evaluation Script
--------------------------------
This script runs test questions against your running RAG backend and computes:
1. Retrieval Quality (Cosine Similarity Score & Relevance)
2. Generation Quality (Keyword Grounding & Answer Completeness)
3. Overall Accuracy Percentage
"""

import json
import urllib.request
import urllib.error
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Test cases based on common PDF documents (e.g. NumPy lab or general docs)
BENCHMARK_TESTS = [
    {
        "question": "What is NumPy?",
        "must_contain": ["library", "numerical", "matrix", "array"],
        "min_similarity": 0.60
    },
    {
        "question": "What are the features of NumPy?",
        "must_contain": ["array", "vectorized", "operations", "efficient", "fast"],
        "min_similarity": 0.60
    },
    {
        "question": "Why are NumPy arrays more efficient than Python lists?",
        "must_contain": ["efficient", "data", "array"],
        "min_similarity": 0.55
    },
]

API_URL = "http://localhost:8000/api/retrieve"


def query_rag_pipeline(question: str) -> dict:
    try:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps({"question": question}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Connecting to {API_URL}: {e}")
        print("-> Make sure your backend is running (`uvicorn backend.main:app --reload --port 8000`)")
        sys.exit(1)


def run_evaluation():
    print("\n" + "=" * 75)
    print(" [RAG ACCURACY BENCHMARK EVALUATION]")
    print("=" * 75)

    passed_count = 0
    total_tests = len(BENCHMARK_TESTS)
    total_similarity_score = 0.0
    total_keyword_score = 0.0

    for idx, test in enumerate(BENCHMARK_TESTS, start=1):
        q = test["question"]
        must_contain = test["must_contain"]
        min_sim = test["min_similarity"]

        print(f"\n[Test #{idx}] Question: '{q}'")
        res = query_rag_pipeline(q)

        answer = res.get("answer", "").strip()
        chunks = res.get("results", [])

        # 1. Retrieval Score
        top_score = chunks[0]["score"] if chunks else 0.0
        total_similarity_score += top_score
        retrieval_ok = top_score >= min_sim and len(chunks) > 0

        # 2. Answer Groundedness / Keyword Match
        answer_lower = answer.lower()
        matched_kw = [kw for kw in must_contain if kw.lower() in answer_lower]
        kw_match_ratio = len(matched_kw) / len(must_contain)
        total_keyword_score += kw_match_ratio
        generation_ok = kw_match_ratio >= 0.40

        # Pass condition
        test_passed = retrieval_ok and generation_ok
        if test_passed:
            passed_count += 1

        print(f"  |- Top Chunk Similarity : {top_score:.4f} (Threshold: >={min_sim}) -> {'[PASS]' if retrieval_ok else '[FAIL]'}")
        print(f"  |- Keyword Match Ratio   : {kw_match_ratio*100:.1f}% ({len(matched_kw)}/{len(must_contain)} matched) -> {'[PASS]' if generation_ok else '[FAIL]'}")
        print(f"  |- Generated Answer     : {answer[:130]}..." if len(answer) > 130 else f"  |- Generated Answer     : {answer}")
        print(f"  |- Test Result          : {'[PASSED]' if test_passed else '[FAILED]'}")

    # Summary calculation
    accuracy_percentage = (passed_count / total_tests) * 100
    avg_similarity = (total_similarity_score / total_tests)
    avg_kw_accuracy = (total_keyword_score / total_tests) * 100

    print("\n" + "=" * 75)
    print(" [FINAL ACCURACY SCORECARD]")
    print("=" * 75)
    print(f"  * Overall Test Pass Rate   : {accuracy_percentage:.1f}% ({passed_count}/{total_tests} Tests Passed)")
    print(f"  * Average Retrieval Score  : {avg_similarity:.4f} / 1.0000")
    print(f"  * Average Concept Accuracy : {avg_kw_accuracy:.1f}%")
    print("=" * 75)

    if accuracy_percentage >= 80:
        print("  >> VERDICT: HIGH ACCURACY (RAG Pipeline is performing accurately)")
    elif accuracy_percentage >= 50:
        print("  >> VERDICT: MODERATE ACCURACY (Consider increasing Top-K or adjusting chunk size)")
    else:
        print("  >> VERDICT: LOW ACCURACY (Check PDF text extraction and embeddings)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_evaluation()
