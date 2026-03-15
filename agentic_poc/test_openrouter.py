import requests

url = "https://openrouter.ai/api/v1/models"
try:
    response = requests.get(url).json()
    free_models = []
    for m in response['data']:
        if ":free" in m['id']:
            free_models.append(m['id'])
    print("Available Free Models:")
    print("\n".join(free_models[:10]))
except Exception as e:
    print(f"Error: {e}")
