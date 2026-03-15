import requests

def search_openml_datasets(query: str = "") -> str:
    """
    Find datasets from OpenML (openml.org) based on a search term.
    Useful for ML dataset recommendations and references.
    Args:
        query: What kind of data to look for, e.g., 'housing' or 'cancer'.
    """
    try:
        # Fetching a raw list of datasets. For a POC, we grab 100 and filter locally by name
        url = "https://www.openml.org/api/v1/json/data/list/status/active/limit/100"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            datasets = data.get("data", {}).get("dataset", [])
            
            # Filter if query provided
            if query:
                datasets = [d for d in datasets if query.lower() in d.get("name", "").lower()]
            
            # Take top 5
            top_datasets = datasets[:5]
            if not top_datasets:
                return f"No simple matches for '{query}' found."
            
            result = []
            for d in top_datasets:
                result.append(f"Name: {d.get('name')} (ID: {d.get('did')}) - openml.org/d/{d.get('did')}")
            
            return "Found the following datasets on OpenML:\n" + "\n".join(result)
        else:
            return f"Failed to fetch from OpenML: HTTP {response.status_code}"
    except Exception as e:
        return f"Error contacting OpenML: {str(e)}"
