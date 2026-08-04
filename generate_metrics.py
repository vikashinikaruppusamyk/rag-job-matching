import json
import os
from pathlib import Path

def analyze_outputs():
    """Analyze all output JSON files and generate metrics."""
    
    print("=" * 70)
    print("METRICS ANALYSIS")
    print("=" * 70 + "\n")
    
    output_files = sorted([f for f in os.listdir('.') if f.startswith('output_') and f.endswith('.json') and f != 'output_sample.json'])
    
    print(f"Found {len(output_files)} output files\n")
    
    all_matches = []
    jd_results = []
    
    for output_file in output_files:
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        jd_title = output_file.replace('output_', '').replace('.json', '')
        top_match = data['top_matches'][0]
        
        print(f"JD: {jd_title}")
        print(f"  Top match: {top_match['candidate_name']}")
        print(f"  Score: {top_match['match_score']}/100")
        print(f"  Skills matched: {len(top_match['matched_skills'])}\n")
        
        # Collect stats
        for match in data['top_matches']:
            all_matches.append({
                'jd': jd_title,
                'candidate': match['candidate_name'],
                'score': match['match_score'],
                'skills': len(match['matched_skills'])
            })
        
        jd_results.append({
            'jd': jd_title,
            'top_score': top_match['match_score'],
            'avg_top_3_score': sum([m['match_score'] for m in data['top_matches'][:3]]) / 3,
            'total_matches': len(data['top_matches'])
        })
    
    # Calculate statistics
    scores = [m['score'] for m in all_matches]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    print("=" * 70)
    print("OVERALL STATISTICS")
    print("=" * 70 + "\n")
    
    print(f"Total matches analyzed: {len(all_matches)}")
    print(f"Average match score: {avg_score:.1f}/100")
    print(f"Highest score: {max_score:.1f}/100")
    print(f"Lowest score: {min_score:.1f}/100")
    print(f"Score range: {max_score - min_score:.1f}\n")
    
    # Skills statistics
    skills_matched = [m['skills'] for m in all_matches]
    avg_skills = sum(skills_matched) / len(skills_matched)
    
    print(f"Average skills matched per candidate: {avg_skills:.1f}")
    print(f"Max skills matched: {max(skills_matched)}")
    print(f"Min skills matched: {min(skills_matched)}\n")
    
    # Job Description performance
    print("=" * 70)
    print("JOB DESCRIPTION PERFORMANCE")
    print("=" * 70 + "\n")
    
    for jd in jd_results:
        print(f"JD: {jd['jd']}")
        print(f"  Top match score: {jd['top_score']:.1f}")
        print(f"  Avg top-3 score: {jd['avg_top_3_score']:.1f}")
        print(f"  Total matches: {jd['total_matches']}\n")
    
    # Generate report
    metrics_report = {
        'project': 'RAG Job Matching System',
        'date': '2026-08-06',
        'summary': {
            'total_resumes': 30,
            'total_embeddings': 333,
            'total_job_descriptions_tested': len(output_files),
            'hybrid_search_weights': {
                'semantic': 0.7,
                'keyword': 0.3
            }
        },
        'performance': {
            'average_match_score': round(avg_score, 2),
            'score_range': {
                'max': round(max_score, 2),
                'min': round(min_score, 2),
                'spread': round(max_score - min_score, 2)
            },
            'skills_matching': {
                'average_per_candidate': round(avg_skills, 2),
                'max_matched': max(skills_matched),
                'min_matched': min(skills_matched)
            }
        },
        'job_descriptions': jd_results,
        'retrieval': {
            'status': 'Working',
            'database_size_embeddings': 333,
            'retrieval_method': 'Semantic search + keyword filtering'
        },
        'data_quality': {
            'resumes_processed': 30,
            'embeddings_generated': 333,
            'average_chunks_per_resume': 11,
            'metadata_extracted': ['name', 'years_exp', 'skills', 'section']
        }
    }
    
    # Save report
    with open('METRICS_REPORT.json', 'w') as f:
        json.dump(metrics_report, f, indent=2)
    
    print("=" * 70)
    print("✓ METRICS REPORT GENERATED")
    print("=" * 70)
    print(f"\nSaved to: METRICS_REPORT.json\n")
    
    return metrics_report

if __name__ == '__main__':
    report = analyze_outputs()