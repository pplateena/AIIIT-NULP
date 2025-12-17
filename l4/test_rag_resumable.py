#!/usr/bin/env python3
"""
Resumable test suite for GT New Horizons RAG System
Saves progress after each test to prevent data loss from quota/rate limits
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict
from test_rag import RAGTester


class ResumableRAGTester(RAGTester):
    def __init__(self, llm_provider='ollama', results_file=None):
        super().__init__(llm_provider)

        # Use timestamped filename if not provided
        if results_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"test_results_resumable_{timestamp}.json"

        self.results_file = results_file
        self.completed_questions = set()

        # Load existing results if file exists
        self.existing_results = self.load_existing_results()

    def load_existing_results(self) -> List[Dict]:
        """Load existing test results if available"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results = data.get('results', [])

                    # Track completed questions
                    for result in results:
                        self.completed_questions.add(result['question'])

                    print(f"📂 Loaded {len(results)} existing results from {self.results_file}")
                    return results
            except Exception as e:
                print(f"⚠️  Error loading existing results: {e}")

        return []

    def save_progress(self, results: List[Dict]):
        """Save current progress to file"""
        try:
            # Generate summary
            summary = self.generate_summary(results)

            output = {
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "llm_provider": self.llm_provider,
                    "total_tests_planned": len(self.get_test_questions()),
                    "total_tests_completed": len(results),
                    "in_progress": True
                },
                "summary": summary,
                "results": results
            }

            # Write to file
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"💾 Progress saved ({len(results)} tests)")

        except Exception as e:
            print(f"❌ Error saving progress: {e}")

    def finalize_results(self, results: List[Dict]):
        """Mark results as complete"""
        try:
            summary = self.generate_summary(results)

            output = {
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "llm_provider": self.llm_provider,
                    "total_tests_planned": len(self.get_test_questions()),
                    "total_tests_completed": len(results),
                    "in_progress": False,
                    "status": "completed"
                },
                "summary": summary,
                "results": results
            }

            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Final results saved to: {self.results_file}")

        except Exception as e:
            print(f"❌ Error finalizing results: {e}")

    def run_resumable_tests(self, start_from: int = 1, show_output: bool = True) -> Dict:
        """Run tests with resumable progress tracking"""
        test_questions = self.get_test_questions()

        print(f"\n🧪 Starting Resumable RAG System Test Suite")
        print(f"Total test cases: {len(test_questions)}")
        print(f"LLM Provider: {self.llm_provider}")
        print(f"Results file: {self.results_file}")

        # Start with existing results
        results = self.existing_results.copy()

        if results:
            print(f"📊 Resuming from previous run ({len(results)} tests already completed)")

        print(f"{'='*80}\n")

        try:
            for i, test_case in enumerate(test_questions, 1):
                # Skip if already completed
                if test_case['question'] in self.completed_questions:
                    print(f"⏭️  Test {i}/{len(test_questions)} - Skipping (already completed)")
                    continue

                # Skip if before start_from
                if i < start_from:
                    print(f"⏭️  Test {i}/{len(test_questions)} - Skipping (starting from {start_from})")
                    continue

                print(f"\n📌 Test {i}/{len(test_questions)}")

                try:
                    result = self.run_single_test(test_case, show_output=show_output)
                    results.append(result)
                    self.completed_questions.add(test_case['question'])

                    # Save progress after each test
                    self.save_progress(results)

                except Exception as e:
                    print(f"❌ Test failed with error: {e}")

                    # Still save the error result
                    error_result = {
                        "timestamp": datetime.now().isoformat(),
                        "category": test_case["category"],
                        "question": test_case["question"],
                        "expected_topics": test_case["expected_topics"],
                        "response": f"Error: {str(e)}",
                        "sources": [],
                        "metrics": {
                            "success": False,
                            "error": str(e),
                            "quality_score": 0
                        }
                    }
                    results.append(error_result)
                    self.save_progress(results)

                    # Check if it's a quota error
                    if 'quota' in str(e).lower() or '429' in str(e):
                        print(f"\n⚠️  QUOTA EXCEEDED - Stopping test run")
                        print(f"Progress saved! Resume later with:")
                        print(f"  python test_rag_resumable.py --resume {self.results_file} --start {i+1}")
                        break

                # Pause between tests
                if i < len(test_questions):
                    time.sleep(5)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Test run interrupted by user")
            print(f"Progress saved! Resume later with:")
            print(f"  python test_rag_resumable.py --resume {self.results_file}")

        # Finalize results
        self.finalize_results(results)

        # Generate summary
        summary = self.generate_summary(results)
        self.print_summary(summary)

        return {
            "results": results,
            "summary": summary
        }


def main():
    """Main test runner with command line args"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Resumable RAG System Tests')
    parser.add_argument('--llm-provider', default='ollama', choices=['gemini', 'claude', 'ollama'],
                       help='LLM provider to use (default: ollama for local mistral)')
    parser.add_argument('--resume', type=str, help='Resume from existing results file')
    parser.add_argument('--start', type=int, default=1, help='Start from test number')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # Check if knowledge base exists
    from rag_pipeline import RAGPipeline
    test_rag = RAGPipeline()
    stats = test_rag.vector_db.get_collection_stats()

    if stats.get('total_chunks', 0) == 0:
        print("❌ Knowledge base is empty! Run 'python main_simple.py build' first.")
        sys.exit(1)

    print(f"✅ Knowledge base ready: {stats.get('total_chunks', 0)} chunks")

    # Create tester
    tester = ResumableRAGTester(
        llm_provider=args.llm_provider,
        results_file=args.resume
    )

    # Run tests
    tester.run_resumable_tests(
        start_from=args.start,
        show_output=not args.quiet
    )


if __name__ == "__main__":
    main()
