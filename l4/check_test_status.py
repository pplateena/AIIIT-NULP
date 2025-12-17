#!/usr/bin/env python3
"""Check status of test runs"""

import json
import sys
import os
from datetime import datetime

def check_status(filename):
    """Check status of a test results file"""
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        test_run = data.get('test_run', {})
        summary = data.get('summary', {})
        results = data.get('results', [])

        print(f"\n{'='*80}")
        print(f"📊 Test Run Status: {filename}")
        print(f"{'='*80}")

        print(f"\n🕐 Timestamp: {test_run.get('timestamp', 'Unknown')}")
        print(f"🤖 LLM Provider: {test_run.get('llm_provider', 'Unknown')}")
        print(f"📝 Tests Completed: {test_run.get('total_tests_completed', 0)}/{test_run.get('total_tests_planned', 0)}")

        status = test_run.get('status', 'in_progress' if test_run.get('in_progress', True) else 'unknown')
        status_emoji = "✅" if status == "completed" else "🔄"
        print(f"{status_emoji} Status: {status.upper()}")

        if summary:
            print(f"\n📈 Summary:")
            print(f"  Successful: {summary.get('successful', 0)}/{summary.get('total_tests', 0)} ({summary.get('success_rate', 0):.1f}%)")
            print(f"  Failed: {summary.get('failed', 0)}")

            if summary.get('avg_quality_score'):
                print(f"  Avg Quality Score: {summary.get('avg_quality_score', 0):.1f}/100")
                print(f"  Avg Query Time: {summary.get('avg_query_time', 0):.2f}s")
                print(f"  Avg Sources: {summary.get('avg_sources', 0):.1f}")

        # List completed tests
        print(f"\n✅ Completed Tests:")
        for i, result in enumerate(results, 1):
            success = result.get('metrics', {}).get('success', False)
            category = result.get('category', 'Unknown')
            question = result.get('question', '')[:60]
            status_icon = "✅" if success else "❌"
            print(f"  {i}. {status_icon} [{category}] {question}...")

        # Show what's next
        if status != 'completed':
            next_test = len(results) + 1
            print(f"\n▶️  Next test to run: {next_test}")
            print(f"\n💡 To resume:")
            print(f"   python test_rag_resumable.py --resume {filename} --start {next_test}")

        print(f"\n{'='*80}")

    except Exception as e:
        print(f"❌ Error reading file: {e}")


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Find most recent test results file
        files = [f for f in os.listdir('.') if f.startswith('test_results')]
        if not files:
            print("❌ No test results files found")
            print("\nUsage: python check_test_status.py [filename]")
            return

        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        filename = files[0]
        print(f"Using most recent file: {filename}")

    check_status(filename)


if __name__ == "__main__":
    main()
