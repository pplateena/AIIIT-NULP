#!/usr/bin/env python3
"""
Test suite for GT New Horizons RAG System
Tests various question types and evaluates response quality
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
from rag_pipeline import RAGPipeline
from markdown_renderer import render_markdown


class RAGTester:
    def __init__(self, llm_provider='ollama'):
        self.llm_provider = llm_provider
        self.rag = RAGPipeline(llm_provider=llm_provider)
        self.test_results = []

    def get_test_questions(self) -> List[Dict[str, str]]:
        """
        Comprehensive test questions covering different difficulty levels and topics
        """
        return [
            # Simple factual questions (should be answered directly from single sources)
            {
                "category": "Simple Factual",
                "question": "What is an Electric Blast Furnace?",
                "expected_topics": ["electric blast furnace", "multiblock", "steel"]
            },
            {
                "category": "Simple Factual",
                "question": "What materials do I need to make steel?",
                "expected_topics": ["steel", "iron", "coal", "carbon"]
            },
            {
                "category": "Simple Factual",
                "question": "What is the difference between LV, MV, and HV power tiers?",
                "expected_topics": ["voltage", "tier", "power", "machines"]
            },

            # Process-oriented questions (require step-by-step information)
            {
                "category": "Process/How-to",
                "question": "How do I set up automated ore processing?",
                "expected_topics": ["automation", "ore", "processing", "machines"]
            },
            {
                "category": "Process/How-to",
                "question": "What are the steps to progress from Steam Age to LV tier?",
                "expected_topics": ["steam", "lv", "progression", "bronze"]
            },
            {
                "category": "Process/How-to",
                "question": "How do I build my first multiblock machine?",
                "expected_topics": ["multiblock", "construction", "blocks"]
            },

            # Technical/mechanical questions
            {
                "category": "Technical",
                "question": "How does the GT power system work?",
                "expected_topics": ["power", "voltage", "amperage", "energy"]
            },
            {
                "category": "Technical",
                "question": "What is the purpose of different cable types?",
                "expected_topics": ["cable", "wire", "voltage", "loss"]
            },
            {
                "category": "Technical",
                "question": "How does ore multiplication work in GT?",
                "expected_topics": ["ore", "processing", "multiplication", "crusher"]
            },

            # Comparison questions
            {
                "category": "Comparison",
                "question": "What are the best early game power sources?",
                "expected_topics": ["power", "generator", "steam", "early"]
            },
            {
                "category": "Comparison",
                "question": "Should I use bronze or steel tools first?",
                "expected_topics": ["bronze", "steel", "tools", "progression"]
            },

            # Complex synthesis questions (require information from multiple sources)
            {
                "category": "Complex Synthesis",
                "question": "What machines and materials do I need for a complete LV setup?",
                "expected_topics": ["lv", "machines", "materials", "setup"]
            },
            {
                "category": "Complex Synthesis",
                "question": "How does the progression system work from start to HV tier?",
                "expected_topics": ["progression", "tier", "steam", "lv", "mv", "hv"]
            },

            # Troubleshooting questions
            {
                "category": "Troubleshooting",
                "question": "Why isn't my machine receiving power?",
                "expected_topics": ["power", "machine", "cable", "voltage"]
            },
            {
                "category": "Troubleshooting",
                "question": "What should I do if my Electric Blast Furnace isn't forming?",
                "expected_topics": ["electric blast furnace", "multiblock", "structure"]
            },

            # Edge cases (might not have direct answers)
            {
                "category": "Edge Case",
                "question": "What is the fastest way to reach end game?",
                "expected_topics": ["progression", "advanced", "tier"]
            },
            {
                "category": "Edge Case",
                "question": "Can I skip the Bronze Age?",
                "expected_topics": ["bronze", "progression", "skip"]
            },

            # Recipe/crafting questions
            {
                "category": "Recipe",
                "question": "How do I craft a steam turbine?",
                "expected_topics": ["steam", "turbine", "craft", "recipe"]
            },
            {
                "category": "Recipe",
                "question": "What ingredients are needed for aluminium production?",
                "expected_topics": ["aluminium", "aluminum", "production", "ore"]
            },

            # Specific item questions
            {
                "category": "Specific Item",
                "question": "What is a Large Steam Turbine used for?",
                "expected_topics": ["turbine", "steam", "power", "generator"]
            },
            {
                "category": "Specific Item",
                "question": "What does the Research Station do?",
                "expected_topics": ["research", "station", "unlock", "recipe"]
            }
        ]

    def evaluate_response(self, question: str, response: str, sources: List[Dict],
                         expected_topics: List[str]) -> Dict:
        """
        Evaluate a single response based on multiple criteria
        """
        response_lower = response.lower()

        # Calculate metrics
        metrics = {
            # Basic metrics
            "response_length_words": len(response.split()),
            "response_length_chars": len(response),
            "num_sources": len(sources),

            # Relevance check (how many expected topics are mentioned)
            "topics_covered": sum(1 for topic in expected_topics if topic.lower() in response_lower),
            "topics_total": len(expected_topics),
            "topic_coverage_ratio": 0.0,

            # Source quality
            "avg_relevance_score": 0.0,
            "has_sources": len(sources) > 0,

            # Response quality indicators
            "has_numbers": any(char.isdigit() for char in response),
            "has_lists": any(marker in response for marker in ['•', '-', '1.', '2.', '*']),
            "has_specific_terms": False,
        }

        if metrics["topics_total"] > 0:
            metrics["topic_coverage_ratio"] = metrics["topics_covered"] / metrics["topics_total"]

        if sources:
            metrics["avg_relevance_score"] = sum(s.get('relevance_score', 0) for s in sources) / len(sources)

        # Check for specific GT New Horizons terms
        gt_terms = ['gregtech', 'gt', 'multiblock', 'tier', 'voltage', 'machine', 'recipe', 'ore']
        metrics["has_specific_terms"] = any(term in response_lower for term in gt_terms)

        # Overall quality score (0-100)
        quality_score = 0
        quality_score += min(metrics["topic_coverage_ratio"] * 40, 40)  # Max 40 points for topic coverage
        quality_score += min(metrics["num_sources"] * 5, 20)  # Max 20 points for sources (4+ sources)
        quality_score += min(metrics["response_length_words"] / 10, 20)  # Max 20 points for length (200+ words)
        quality_score += 10 if metrics["has_lists"] else 0  # 10 points for structured response
        quality_score += 10 if metrics["has_specific_terms"] else 0  # 10 points for domain terms

        metrics["quality_score"] = min(quality_score, 100)

        return metrics

    def run_single_test(self, test_case: Dict, show_output: bool = True) -> Dict:
        """Run a single test case"""
        question = test_case["question"]
        category = test_case["category"]
        expected_topics = test_case["expected_topics"]

        if show_output:
            print(f"\n{'='*80}")
            print(f"Category: {category}")
            print(f"Question: {question}")
            print(f"Expected topics: {', '.join(expected_topics)}")
            print(f"{'='*80}")

        # Time the query
        start_time = time.time()

        try:
            response, sources = self.rag.generate_response(question, use_history=False)
            query_time = time.time() - start_time

            if show_output:
                print(f"\n📝 Response ({query_time:.2f}s):")
                print(render_markdown(response))

                if sources:
                    print(f"\n📚 Sources ({len(sources)}):")
                    for i, source in enumerate(sources, 1):
                        print(f"  {i}. {source['title']} (relevance: {source['relevance_score']:.3f})")
                        print(f"     {source['url']}")

            # Evaluate response
            metrics = self.evaluate_response(question, response, sources, expected_topics)
            metrics["query_time"] = query_time
            metrics["success"] = True
            metrics["error"] = None

            if show_output:
                print(f"\n📊 Evaluation:")
                print(f"  Quality Score: {metrics['quality_score']:.1f}/100")
                print(f"  Topics Covered: {metrics['topics_covered']}/{metrics['topics_total']} ({metrics['topic_coverage_ratio']*100:.0f}%)")
                print(f"  Sources Used: {metrics['num_sources']}")
                print(f"  Response Length: {metrics['response_length_words']} words")
                print(f"  Avg Relevance: {metrics['avg_relevance_score']:.3f}")

        except Exception as e:
            query_time = time.time() - start_time
            response = f"Error: {str(e)}"
            sources = []
            metrics = {
                "success": False,
                "error": str(e),
                "query_time": query_time,
                "quality_score": 0
            }

            if show_output:
                print(f"\n❌ Error: {e}")

        # Store result
        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "question": question,
            "expected_topics": expected_topics,
            "response": response,
            "sources": [
                {
                    "title": s.get('title', ''),
                    "url": s.get('url', ''),
                    "relevance": s.get('relevance_score', 0)
                } for s in sources
            ],
            "metrics": metrics
        }

        return result

    def run_all_tests(self, show_output: bool = True, save_results: bool = True) -> Dict:
        """Run all test cases and generate report"""
        test_questions = self.get_test_questions()

        print(f"\n🧪 Starting RAG System Test Suite")
        print(f"Total test cases: {len(test_questions)}")
        print(f"LLM Provider: {self.llm_provider}")
        print(f"{'='*80}\n")

        results = []
        for i, test_case in enumerate(test_questions, 1):
            print(f"\n📌 Test {i}/{len(test_questions)}")
            result = self.run_single_test(test_case, show_output=show_output)
            results.append(result)

            # Brief pause between tests (increased to avoid rate limits)
            if i < len(test_questions):
                time.sleep(5)  # 5 second delay = max 12 requests/min, safely under 15 RPM limit

        # Generate summary statistics
        summary = self.generate_summary(results)

        # Save results
        if save_results:
            self.save_results(results, summary)

        return {
            "results": results,
            "summary": summary
        }

    def generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from test results"""
        successful = [r for r in results if r["metrics"].get("success", False)]
        failed = [r for r in results if not r["metrics"].get("success", False)]

        summary = {
            "total_tests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
        }

        if successful:
            summary["avg_quality_score"] = sum(r["metrics"]["quality_score"] for r in successful) / len(successful)
            summary["avg_query_time"] = sum(r["metrics"]["query_time"] for r in successful) / len(successful)
            summary["avg_sources"] = sum(r["metrics"]["num_sources"] for r in successful) / len(successful)
            summary["avg_response_length"] = sum(r["metrics"]["response_length_words"] for r in successful) / len(successful)
            summary["avg_topic_coverage"] = sum(r["metrics"]["topic_coverage_ratio"] for r in successful) / len(successful) * 100

            # Category breakdown
            categories = {}
            for result in successful:
                cat = result["category"]
                if cat not in categories:
                    categories[cat] = {"count": 0, "total_quality": 0}
                categories[cat]["count"] += 1
                categories[cat]["total_quality"] += result["metrics"]["quality_score"]

            summary["by_category"] = {
                cat: {
                    "count": data["count"],
                    "avg_quality": data["total_quality"] / data["count"]
                }
                for cat, data in categories.items()
            }

        return summary

    def save_results(self, results: List[Dict], summary: Dict):
        """Save test results to JSON file"""
        output = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "llm_provider": self.llm_provider,
                "total_tests": len(results)
            },
            "summary": summary,
            "results": results
        }

        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {filename}")

    def print_summary(self, summary: Dict):
        """Print formatted summary"""
        print(f"\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")

        if summary.get('avg_quality_score'):
            print(f"\n🎯 Quality Metrics:")
            print(f"  Average Quality Score: {summary['avg_quality_score']:.1f}/100")
            print(f"  Average Query Time: {summary['avg_query_time']:.2f}s")
            print(f"  Average Sources: {summary['avg_sources']:.1f}")
            print(f"  Average Response Length: {summary['avg_response_length']:.0f} words")
            print(f"  Average Topic Coverage: {summary['avg_topic_coverage']:.1f}%")

        if summary.get('by_category'):
            print(f"\n📂 By Category:")
            for category, data in sorted(summary['by_category'].items()):
                print(f"  {category}: {data['count']} tests, avg quality {data['avg_quality']:.1f}/100")

        print(f"{'='*80}")


def main():
    """Main test runner"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Test GT New Horizons RAG System')
    parser.add_argument('--llm-provider', choices=['ollama', 'gemini', 'claude'],
                        default='ollama', help='LLM provider to use (default: ollama)')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    args = parser.parse_args()

    # Check if knowledge base exists
    tester = RAGTester(llm_provider=args.llm_provider)
    stats = tester.rag.vector_db.get_collection_stats()

    if stats.get('total_chunks', 0) == 0:
        print("❌ Knowledge base is empty! Run 'python main_simple.py build' first.")
        sys.exit(1)

    print(f"✅ Knowledge base ready: {stats.get('total_chunks', 0)} chunks")

    # Run tests
    test_output = tester.run_all_tests(show_output=not args.quiet, save_results=True)

    # Print summary
    tester.print_summary(test_output['summary'])


if __name__ == "__main__":
    main()
