import os
from job_matcher import run_job_matcher

jd_folder = './data/job_descriptions'
jd_files = sorted([f for f in os.listdir(jd_folder) if f.endswith('.txt')])

print(f"Found {len(jd_files)} job descriptions\n")

for i, jd_file in enumerate(jd_files, 1):
    jd_path = os.path.join(jd_folder, jd_file)
    output_file = f'output_{i:02d}_{jd_file.replace(".txt", ".json")}'
    
    with open(jd_path, 'r') as f:
        jd_text = f.read()
    
    print(f"\n{'='*70}")
    print(f"JD {i}: {jd_file}")
    print(f"{'='*70}")
    
    output = run_job_matcher(jd_text, top_k=10, output_file=output_file)
    
    print(f"\n✓ Top 3 matches for {jd_file}:")
    for match in output['top_matches'][:3]:
        print(f"  {match['candidate_name']}: {match['match_score']}/100")