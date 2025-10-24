#!/usr/bin/env python3
"""
AURELIA System Evaluation Script
Tests deployed FastAPI system for Lab 5

Evaluates:
- Quality: Completeness, citations, accuracy
- Performance: Cached vs uncached latency
- Cost: API usage estimates
"""

import os
import time
import json
import requests
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment from root
root_dir = Path(__file__).parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
API_URL = os.getenv("API_URL", "https://aurelia-api-uxds3rw7za-ue.a.run.app")
REPORT_DIR = Path(__file__).parent / "reports"

# Test concepts
QUALITY_TEST_CONCEPTS = [
    "Duration",
    "Black-Scholes Model", 
    "Internal Rate of Return",
    "Sharpe Ratio",
    "Bond Convexity",
    "Modified Duration",
    "Yield Curve",
    "Option Greeks"
]

PERFORMANCE_TEST_CONCEPTS = [
    "Sharpe Ratio",
    "Convexity", 
    "Yield Curve"
]

WIKIPEDIA_TEST_CONCEPTS = [
    "Cryptocurrency",
    "Hedge Fund"
]

print("="*70)
print("AURELIA SYSTEM EVALUATION")
print("="*70)
print(f"API URL: {API_URL}")
print(f"Report Directory: {REPORT_DIR}")
print()

# Ensure report directory exists
REPORT_DIR.mkdir(exist_ok=True)


def call_api(endpoint: str, data: Dict = None, method: str = "GET") -> Tuple[Dict, float]:
    """Call API and measure latency"""
    url = f"{API_URL}{endpoint}"
    
    start = time.perf_counter()
    
    if method == "GET":
        response = requests.get(url)
    else:
        response = requests.post(url, json=data)
    
    latency_ms = (time.perf_counter() - start) * 1000.0
    
    response.raise_for_status()
    return response.json(), latency_ms


def evaluate_completeness(note: Dict) -> Dict[str, Any]:
    """Evaluate note completeness"""
    required_fields = {
        'concept': note.get('concept'),
        'definition': note.get('definition'),
        'key_points': note.get('key_points'),
    }
    
    optional_fields = {
        'matlab_functions': note.get('matlab_functions'),
        'examples': note.get('examples'),
        'formulas': note.get('formulas'),
        'related_concepts': note.get('related_concepts'),
        'practical_applications': note.get('practical_applications')
    }
    
    score = 0
    max_score = 0
    details = {}
    
    # Check required fields (2 points each)
    for field, value in required_fields.items():
        max_score += 2
        if value:
            if isinstance(value, list):
                has_content = len(value) > 0
            else:
                has_content = len(str(value)) > 0
            
            if has_content:
                score += 2
                details[field] = "✅ Present"
            else:
                details[field] = "⚠️ Empty"
        else:
            details[field] = "❌ Missing"
    
    # Check optional fields (1 point each)
    for field, value in optional_fields.items():
        max_score += 1
        if value:
            if isinstance(value, list):
                has_content = len(value) > 0
            else:
                has_content = len(str(value)) > 0
            
            if has_content:
                score += 1
                details[field] = "✅ Present"
    
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    return {
        "score": percentage,
        "details": details,
        "score_breakdown": f"{score}/{max_score}"
    }


def evaluate_citations(response: Dict) -> Dict[str, Any]:
    """Evaluate citation quality"""
    sources_used = response.get('sources_used', [])
    
    if not sources_used:
        return {
            "score": 0,
            "details": "No citations provided",
            "citation_count": 0
        }
    
    score = 0
    max_score = len(sources_used) * 10
    details = []
    
    for citation in sources_used:
        citation_score = 0
        citation_lower = citation.lower()
        
        # Check for page reference
        if 'page' in citation_lower or 'p.' in citation_lower:
            citation_score += 4
        
        # Check for section/chapter
        if 'section' in citation_lower or 'chapter' in citation_lower:
            citation_score += 3
        
        # Check for source mention
        if 'fintbx' in citation_lower or 'pdf' in citation_lower or 'wikipedia' in citation_lower:
            citation_score += 3
        
        details.append({
            "citation": citation[:100],
            "score": citation_score
        })
        score += citation_score
    
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    return {
        "score": percentage,
        "details": details,
        "citation_count": len(sources_used)
    }


def evaluate_accuracy(concept: str, response: Dict) -> Dict[str, Any]:
    """Evaluate accuracy heuristics"""
    note = response.get('note', {})
    definition = note.get('definition', '') or ''
    source = response.get('source', '')
    
    checks = {
        'has_definition': len(definition) > 50,
        'definition_length_reasonable': 50 < len(definition) < 1500,
        'mentions_concept': concept.lower() in definition.lower(),
        'has_technical_content': any(
            term in definition.lower() 
            for term in ['calculate', 'formula', 'measure', 'rate', 'risk', 'return', 'financial', 'investment']
        ),
        'from_primary_source': source == 'fintbx'
    }
    
    score = sum(1 for v in checks.values() if v) / len(checks) * 100
    
    return {
        "score": score,
        "checks": checks,
        "source": source
    }


def test_quality() -> Dict[str, Any]:
    """Test quality metrics"""
    print("\n" + "="*70)
    print("QUALITY EVALUATION")
    print("="*70)
    
    results = []
    
    for i, concept in enumerate(QUALITY_TEST_CONCEPTS, 1):
        print(f"\n[{i}/{len(QUALITY_TEST_CONCEPTS)}] Testing: {concept}")
        
        try:
            response, latency = call_api("/query", {"concept": concept}, "POST")
            
            completeness = evaluate_completeness(response.get('note', {}))
            citations = evaluate_citations(response)
            accuracy = evaluate_accuracy(concept, response)
            
            result = {
                "concept": concept,
                "completeness": completeness["score"],
                "citation_fidelity": citations["score"],
                "accuracy": accuracy["score"],
                "source": response.get('source'),
                "cached": response.get('cached', False),
                "latency_ms": latency
            }
            
            results.append(result)
            
            print(f"  ✅ Completeness: {completeness['score']:.1f}%")
            print(f"  ✅ Citations: {citations['score']:.1f}%")
            print(f"  ✅ Accuracy: {accuracy['score']:.1f}%")
            print(f"  📊 Source: {response.get('source')}")
            print(f"  ⏱️  Latency: {latency:.0f}ms")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "concept": concept,
                "error": str(e)
            })
    
    avg_completeness = statistics.mean([r.get('completeness', 0) for r in results if 'completeness' in r])
    avg_citations = statistics.mean([r.get('citation_fidelity', 0) for r in results if 'citation_fidelity' in r])
    avg_accuracy = statistics.mean([r.get('accuracy', 0) for r in results if 'accuracy' in r])
    
    return {
        "individual_results": results,
        "averages": {
            "completeness": avg_completeness,
            "citation_fidelity": avg_citations,
            "accuracy": avg_accuracy
        }
    }


def test_performance() -> Dict[str, Any]:
    """Test performance metrics"""
    print("\n" + "="*70)
    print("PERFORMANCE EVALUATION")
    print("="*70)
    
    # Test uncached performance
    print("\n🔄 Testing UNCACHED performance...")
    uncached_results = []
    
    for concept in PERFORMANCE_TEST_CONCEPTS:
        print(f"  Testing: {concept}")
        
        # Force refresh to measure uncached
        response, latency = call_api("/query", {"concept": concept, "force_refresh": True}, "POST")
        
        uncached_results.append({
            "concept": concept,
            "latency_ms": latency
        })
        
        print(f"    ⏱️  Uncached: {latency:.0f}ms")
    
    # Test cached performance
    print("\n💾 Testing CACHED performance...")
    cached_results = []
    
    for concept in PERFORMANCE_TEST_CONCEPTS:
        print(f"  Testing: {concept} (should hit cache)")
        
        # Run 3 times to get average
        latencies = []
        for i in range(3):
            response, latency = call_api("/query", {"concept": concept}, "POST")
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        
        cached_results.append({
            "concept": concept,
            "latency_ms": avg_latency,
            "cached": response.get('cached', False)
        })
        
        print(f"    ⏱️  Cached: {avg_latency:.0f}ms (cached={response.get('cached', False)})")
    
    # Calculate speedup
    avg_uncached = statistics.mean([r['latency_ms'] for r in uncached_results])
    avg_cached = statistics.mean([r['latency_ms'] for r in cached_results])
    speedup = avg_uncached / avg_cached if avg_cached > 0 else 0
    
    print(f"\n📊 Summary:")
    print(f"  Uncached average: {avg_uncached:.0f}ms")
    print(f"  Cached average: {avg_cached:.0f}ms")
    print(f"  Cache speedup: {speedup:.1f}x")
    
    return {
        "uncached": {
            "results": uncached_results,
            "average_latency_ms": avg_uncached
        },
        "cached": {
            "results": cached_results,
            "average_latency_ms": avg_cached
        },
        "speedup": speedup
    }


def test_wikipedia_fallback() -> Dict[str, Any]:
    """Test Wikipedia fallback"""
    print("\n" + "="*70)
    print("WIKIPEDIA FALLBACK TEST")
    print("="*70)
    
    results = []
    
    for concept in WIKIPEDIA_TEST_CONCEPTS:
        print(f"\n🌐 Testing: {concept}")
        
        try:
            response, latency = call_api("/query", {"concept": concept}, "POST")
            
            result = {
                "concept": concept,
                "source": response.get('source'),
                "success": response.get('source') == 'wikipedia',
                "latency_ms": latency
            }
            
            results.append(result)
            
            print(f"  ✅ Source: {response.get('source')}")
            print(f"  ⏱️  Latency: {latency:.0f}ms")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "concept": concept,
                "error": str(e)
            })
    
    return {"results": results}


def estimate_costs(quality_results: Dict, performance_results: Dict) -> Dict[str, Any]:
    """Estimate API costs"""
    # Count queries
    quality_queries = len([r for r in quality_results['individual_results'] if 'completeness' in r])
    uncached_queries = len(performance_results['uncached']['results'])
    cached_queries = len(performance_results['cached']['results']) * 3  # 3 iterations each
    
    total_queries = quality_queries + uncached_queries + cached_queries
    
    # Estimate costs (very rough)
    # Uncached query: ~$0.001 (embedding + generation)
    # Cached query: ~$0 (no OpenAI calls)
    
    uncached_cost = (quality_queries + uncached_queries) * 0.001
    cached_cost = 0  # No OpenAI calls for cached
    
    total_cost = uncached_cost + cached_cost
    
    return {
        "total_queries": total_queries,
        "uncached_queries": quality_queries + uncached_queries,
        "cached_queries": cached_queries,
        "estimated_cost_usd": total_cost,
        "cost_per_uncached_query": 0.001,
        "cost_per_cached_query": 0.0,
        "note": "Rough estimates - actual costs may vary"
    }


def generate_reports(results: Dict[str, Any]):
    """Generate JSON and Markdown reports"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_path = REPORT_DIR / f"evaluation_report_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ JSON report: {json_path}")
    
    # Markdown report
    md_path = REPORT_DIR / f"evaluation_report_{timestamp}.md"
    
    with open(md_path, 'w') as f:
        f.write("# AURELIA System Evaluation Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**API URL:** {API_URL}\n\n")
        
        # Quality Metrics
        f.write("## Quality Metrics\n\n")
        quality = results['quality_metrics']
        f.write(f"- **Average Completeness:** {quality['averages']['completeness']:.1f}%\n")
        f.write(f"- **Average Citation Fidelity:** {quality['averages']['citation_fidelity']:.1f}%\n")
        f.write(f"- **Average Accuracy:** {quality['averages']['accuracy']:.1f}%\n\n")
        
        f.write("### Individual Results\n\n")
        f.write("| Concept | Completeness | Citations | Accuracy | Source | Latency |\n")
        f.write("|---------|--------------|-----------|----------|--------|----------|\n")
        for r in quality['individual_results']:
            if 'completeness' in r:
                f.write(f"| {r['concept']} | {r['completeness']:.1f}% | {r['citation_fidelity']:.1f}% | "
                       f"{r['accuracy']:.1f}% | {r['source']} | {r['latency_ms']:.0f}ms |\n")
        f.write("\n")
        
        # Performance Metrics
        f.write("## Performance Metrics\n\n")
        perf = results['performance_metrics']
        f.write(f"- **Uncached Average:** {perf['uncached']['average_latency_ms']:.0f}ms\n")
        f.write(f"- **Cached Average:** {perf['cached']['average_latency_ms']:.0f}ms\n")
        f.write(f"- **Cache Speedup:** {perf['speedup']:.1f}x\n\n")
        
        # Wikipedia Fallback
        if 'wikipedia_fallback' in results:
            f.write("## Wikipedia Fallback\n\n")
            wiki = results['wikipedia_fallback']
            for r in wiki['results']:
                if 'source' in r:
                    f.write(f"- **{r['concept']}:** {r['source']} ({r['latency_ms']:.0f}ms)\n")
        f.write("\n")
        
        # Cost Analysis
        f.write("## Cost Analysis\n\n")
        cost = results['cost_analysis']
        f.write(f"- **Total Queries:** {cost['total_queries']}\n")
        f.write(f"- **Uncached Queries:** {cost['uncached_queries']}\n")
        f.write(f"- **Cached Queries:** {cost['cached_queries']}\n")
        f.write(f"- **Estimated Total Cost:** ${cost['estimated_cost_usd']:.4f}\n")
        f.write(f"- **Cost per Uncached Query:** ${cost['cost_per_uncached_query']:.4f}\n")
        f.write(f"- **Cost per Cached Query:** ${cost['cost_per_cached_query']:.4f}\n\n")
        f.write(f"_{cost['note']}_\n")
    
    print(f"✅ Markdown report: {md_path}")


def main():
    """Run full evaluation"""
    print("\n🚀 Starting evaluation...\n")
    
    # Check API health
    try:
        health, _ = call_api("/health")
        print(f"✅ API Status: {health.get('status')}")
        print(f"   Pinecone: {health.get('pinecone')}")
        print(f"   PostgreSQL: {health.get('postgres')}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        print("Exiting...")
        return
    
    # Run tests
    quality_results = test_quality()
    performance_results = test_performance()
    wikipedia_results = test_wikipedia_fallback()
    cost_analysis = estimate_costs(quality_results, performance_results)
    
    # Compile results
    results = {
        "timestamp": datetime.now().isoformat(),
        "api_url": API_URL,
        "quality_metrics": quality_results,
        "performance_metrics": performance_results,
        "wikipedia_fallback": wikipedia_results,
        "cost_analysis": cost_analysis
    }
    
    # Generate reports
    generate_reports(results)
    
    print("\n" + "="*70)
    print("✅ EVALUATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"  Quality: {quality_results['averages']['completeness']:.1f}% completeness")
    print(f"  Performance: {performance_results['speedup']:.1f}x cache speedup")
    print(f"  Cost: ${cost_analysis['estimated_cost_usd']:.4f} for {cost_analysis['total_queries']} queries")
    print(f"\n📁 Reports saved to: {REPORT_DIR}/")


if __name__ == "__main__":
    main()