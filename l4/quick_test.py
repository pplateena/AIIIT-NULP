#!/usr/bin/env python3
"""Quick test with just 5 questions"""

from test_rag import RAGTester
from config import Config

def main():
    # Use the provider from .env file
    tester = RAGTester(llm_provider=Config.DEFAULT_LLM_PROVIDER)

    # Run just first 5 tests
    all_questions = tester.get_test_questions()
    quick_questions = all_questions[:5]

    print(f"\n🚀 Running Quick Test ({len(quick_questions)} questions)\n")

    results = []
    for i, test_case in enumerate(quick_questions, 1):
        print(f"\n📌 Test {i}/{len(quick_questions)}")
        result = tester.run_single_test(test_case, show_output=True)
        results.append(result)

    # Show summary
    summary = tester.generate_summary(results)
    tester.print_summary(summary)

if __name__ == "__main__":
    main()
