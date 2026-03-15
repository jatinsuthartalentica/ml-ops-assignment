from typing import Annotated

# Simple tools for the agent to use
def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression.
    Useful for answering math questions.
    Args:
        expression: A string containing a valid math setup like "5 * 4" or "100 / 2".
    """
    try:
        # Warning: eval is dangerous in prod. Fine for this local POC.
        # In prod, we'd use a safer parser like Python's `ast.literal_eval` or a managed tool.
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

def get_system_status() -> str:
    """
    Returns the mocked status of the enterprise system.
    Useful for questions like "How is the system performing?"
    """
    return "All enterprise systems are fully operational. API Latency: 45ms. CPU Usage: 22%."

from app.rag import retrieve_internal_document
from app.openml_tool import search_openml_datasets

# List of all tools to bind to the model later
AGENT_TOOLS = [calculate, get_system_status, retrieve_internal_document, search_openml_datasets]
