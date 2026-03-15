import os
import uuid
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.tools import AGENT_TOOLS

from typing import Annotated, Sequence
from typing_extensions import TypedDict
import operator

class AgentState(TypedDict):
    """The state of the agent's conversation."""
    messages: Annotated[Sequence[BaseMessage], operator.add]

def should_continue(state: AgentState):
    """Determines whether to call a tool or end the interaction."""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

class FakeAgentLLM:
    """A mock LLM that returns simulated tool calls for testing the LangGraph POC without API keys."""
    def bind_tools(self, tools):
        return self
        
    def invoke(self, messages):
        # Extract the original user message and the last message
        user_msg = ""
        for m in messages:
            if getattr(m, 'type', '') == 'human':
                user_msg = m.content.lower()
        
        last_msg = messages[-1]
        
        # If we are returning from a tool node
        if getattr(last_msg, 'type', '') == 'tool':
            return AIMessage(content=f"**[MOCK MODE]** Analysis of tool output: {last_msg.content}")

        # Simulate routing to tools based on keywords and extract args from prompt
        import re
        if "calculate" in user_msg or "*" in user_msg or "+" in user_msg or "total" in user_msg or "deploy" in user_msg or "memory" in user_msg:
            # Try to grab numbers out of the string roughly
            numbers = re.findall(r'\d+', user_msg)
            if len(numbers) >= 2:
                # If they ask about deploying clusters/memory, they want multiplication
                if "times" in user_msg or "*" in user_msg or "deploy" in user_msg or "memory" in user_msg:
                    expr = f"{numbers[0]} * {numbers[1]}"
                else:
                    expr = f"{numbers[0]} + {numbers[1]}"
            else:
                expr = "15 * 24" # fallback
            import uuid
            return AIMessage(content="", tool_calls=[{'name': 'calculate', 'args': {'expression': expr}, 'id': f"call_{uuid.uuid4().hex[:4]}_1"}])
            
        elif "policy" in user_msg or "pto" in user_msg:
            import uuid
            return AIMessage(content="", tool_calls=[{'name': 'retrieve_internal_document', 'args': {'query': 'company remote work pto policy'}, 'id': f"call_{uuid.uuid4().hex[:4]}_2"}])
            
        elif "openml" in user_msg or "dataset" in user_msg:
            import uuid
            return AIMessage(content="", tool_calls=[{'name': 'search_openml_datasets', 'args': {'query': 'diabetes'}, 'id': f"call_{uuid.uuid4().hex[:4]}_3"}])
            
        elif "latency" in user_msg or "api calls" in user_msg or "system" in user_msg:
             import uuid
             return AIMessage(content="", tool_calls=[{'name': 'get_system_status', 'args': {}, 'id': f"call_{uuid.uuid4().hex[:4]}_4"}])
             
        else:
            return AIMessage(content="**[MOCK MODE]** I am running offline without an API key! Ask me to **calculate** something, check a **policy**, or search **OpenML** to see my tool orchestration simulated.")

# Global variable to hold the compiled graph
_agent_app = None

def get_agent_app():
    """Lazily initialize the agent to prevent API Key crashes on boot."""
    global _agent_app
    if _agent_app is None:
        import os
        from langchain_openai import ChatOpenAI
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # 1. Try generic OpenAI key
        if os.getenv("OPENAI_API_KEY"):
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)
            
        # 2. Try OpenRouter (needs custom base URL)
        elif os.getenv("OPENROUTER_API_KEY"):
            llm = ChatOpenAI(
                model_name="meta-llama/llama-3-8b-instruct:free",
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1
            )
            
        # 3. Try Gemini key
        elif os.getenv("GOOGLE_API_KEY"):
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1)
            
        # 4. Fallback to offline Mock Mode if no keys exist
        else:
            llm = FakeAgentLLM()
        
        llm_with_tools = llm.bind_tools(AGENT_TOOLS)
        
        def run_agent(state: AgentState):
            messages = state["messages"]
            system_prompt = SystemMessage(
                content="""You are a helpful enterprise MLOps AI Assistant. 
                You have access to tools. ALWAYS use tools when answering factual questions or doing math. 
                If you don't know the answer, say so. Keep your answers concise."""
            )
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [system_prompt] + list(messages)
            
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
            
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", run_agent)
        
        tool_node = ToolNode(AGENT_TOOLS)
        workflow.add_node("tools", tool_node)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")
        
        _agent_app = workflow.compile()
        
    return _agent_app

def invoke_agent(message: str) -> str:
    """Wrapper to invoke the agent safely."""
    from langchain_core.messages import HumanMessage
    try:
        app_graph = get_agent_app()
        messages = [HumanMessage(content=message)]
        result = app_graph.invoke({"messages": messages})
        return result["messages"][-1].content
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Authentication" in error_msg:
            return "⚠️ Authentication Error: Your OpenAI API Key is invalid or missing."
        return f"⚠️ Agent Error: {error_msg}"
