import requests

url = "https://openrouter.ai/api/v1/models"
try:
    response = requests.get(url).json()
    for m in response['data']:
        if ":free" in m['id']:
            if 'endpoints' in m and any('tools' in e or 'function' in e for e in str(m['endpoints']).lower()):
                print("Might support tools:", m['id'])
            # Many times we can check context_length or architecture
            # Just print the first 5 free models
    print([m['id'] for m in response['data'] if ":free" in m['id']][:10])
except Exception as e:
    print(f"Error: {e}")
