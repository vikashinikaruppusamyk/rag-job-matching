import json

with open('embeddings_cache.json', 'r') as f:
    data = json.load(f)

print(f'✓ Cache file loaded: {len(data)} embeddings')

first_key = list(data.keys())[0]
first_embedding = data[first_key]['embedding']
print(f'✓ First embedding vector size: {len(first_embedding)}')

metadata = data[first_key]['metadata']
print(f'✓ Name: {metadata["name"]}')
print(f'✓ Years: {metadata["years_exp"]}')
print(f'✓ Skills: {metadata["skills"]}')