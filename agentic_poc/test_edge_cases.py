import requests

url = "http://127.0.0.1:8000/chat"

prompts = [
    ("Fallback (No Keywords)", "Hello, what is your name?"),
    ("Math without Digits (Regex failure)", "Can you calculate ten times five?"),
    ("OpenML generic (No specific dataset)", "I need some machine learning datasets from openml."),
    ("Keyword Collision (Precedence Test)", "Search openml for the calculate policy.")
]

for name, msg in prompts:
    print(f"\n--- Testing: {name} ---")
    print(f"Prompt: {msg}")
    try:
        response = requests.post(url, json={"message": msg}).json()
        print(f"Response: {response['response']}")
    except Exception as e:
        print(f"Error: {e}")

