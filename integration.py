import os
import requests
import asyncio
import logging
from typing import Any, Dict, List
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
# ----------
from composio import Composio
from composio.exceptions import ValidationError

class MyState(MessagesState):
    bot_id: str
    response_type: str
    test_output: int

# ---------- COMPOSIO HELPER FUNCTIONS ----------
def _extract_client_config(server: Any) -> Dict[str, Any]:
    """
    Normalise the server response to the config shape expected by MultiServerMCPClient.
    """
    # Collect possible dictionary representations from the server object.
    candidate_maps = []
    transport_fallback = "streamable_http"
    if hasattr(server, "mcp_url"):
        return {"url": getattr(server, "mcp_url"), "transport": transport_fallback}
    if hasattr(server, "client_config") and getattr(server, "client_config"):
        return getattr(server, "client_config")
    if hasattr(server, "model_dump"):
        candidate_maps.append(server.model_dump())
    if hasattr(server, "dict"):
        candidate_maps.append(server.dict())
    if isinstance(server, dict):
        candidate_maps.append(server)
    if hasattr(server, "__dict__"):
        candidate_maps.append({k: getattr(server, k) for k in vars(server) if not k.startswith("_")})

    for data in candidate_maps:
        if not isinstance(data, dict):
            continue
        for key in ("client_config", "clientConfig"):
            value = data.get(key)
            if isinstance(value, dict):
                return value
        # Some responses already match the expected schema (url + transport).
        if {"url", "transport"} <= data.keys():
            return data
        if "mcp_url" in data:
            transport = data.get("type") or transport_fallback
            return {"url": data["mcp_url"], "transport": transport}

    raise ValueError("Could not determine MCP client configuration from server response.")

def _find_existing_server(composio_client: Composio, server_name: str):
    """
    Look up an existing MCP server with the given name.
    """
    response = composio_client.mcp.list(name=server_name)
    items = response.get("items", []) if isinstance(response, dict) else getattr(response, "items", [])
    for entry in items:
        entry_name = entry.get("name") if isinstance(entry, dict) else getattr(entry, "name", None)
        if entry_name == server_name:
            return entry
    return None
# ---------- [END] COMPOSIO HELPER FUNCTIONS [END] ----------
def _coerce_message_content(message: Any) -> str:
    """
    Convert LangChain message/content objects into a serialisable string.
    """
    if message is None:
        return ""
    if isinstance(message, str):
        return message

    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_value = item.get("text") or item.get("content")
                if text_value:
                    parts.append(str(text_value))
        return "\n".join(parts)

    return str(content)

def initialize_composio_mcp():
    logger.info("Preparing Composio MCP client setup")
    composio_client = Composio(api_key=os.environ["COMPOSIO_API_KEY"])

    server_name = "mcp-config-73840"
    logger.debug("Using Composio server name %s", server_name)

    created_new = True
    try:
        logger.info("Creating MCP server %s", server_name)
        server = composio_client.mcp.create(
            name=server_name,
            toolkits=[
                {
                    "toolkit": "googlecalendar",
                    "auth_config": "ac_FKnlhoa1rCHO",
                }
            ],
        )
        logger.info("Successfully created MCP server %s", server_name)
    except ValidationError as exc:
        cause = getattr(exc, "__cause__", None)
        cause_text = str(cause) if cause else str(exc)
        if "already exists" not in cause_text.lower():
            raise
        logger.info("Server %s already exists; attempting to reuse configuration", server_name)
        created_new = False
        server = _find_existing_server(composio_client, server_name)
        if server is None:
            logger.error("Server %s already exists but could not be retrieved", server_name)
            raise RuntimeError(
                f"MCP server named {server_name!r} already exists, but could not retrieve it."
            ) from exc

    server_id = getattr(server, "id", None)
    if server_id is None and isinstance(server, dict):
        server_id = server.get("id")
    if server_id:
        status = "created" if created_new else "reused existing"
        logger.info("Server ready (%s): %s", status, server_id)
    else:
        logger.warning("Server ready but id unavailable in response")

    client_config = _extract_client_config(server)
    if "url" not in client_config or "transport" not in client_config:
        raise ValueError(f"Client config missing url/transport keys: {client_config}")
    logger.debug(
        "Resolved client config for %s: url=%s, transport=%s",
        server_name,
        client_config.get("url"),
        client_config.get("transport"),
    )
    return client_config

    # mcp_client = MultiServerMCPClient({"google_calendar": client_config})
    # mcp_tools = asyncio.run(mcp_client.get_tools())


# --- Configuration ---
MODEL_NAME = "gpt-5-nano"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialize LLM ---
llm = ChatOpenAI(model_name=MODEL_NAME)

client_config = initialize_composio_mcp()

# --- Initialize MCP Client ---
mcp_client = MultiServerMCPClient({
    "github": {
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "streamable_http",
        "headers": {
            "Authorization": f"Bearer {os.environ['GITHUB_PAT']}"
        }
    },
    "google_calendar": client_config,
})

# --- Tool Definitions ---
@tool
def get_weather(city: str) -> str:
    """Example synchronous tool: returns weather info for a city."""
    return f"It's always sunny in {city}!"

local_tools = [get_weather]

# --- Node Definitions ---
async def load_mcp_tools():
    """Load MCP tools asynchronously"""
    logger.info("Requesting MCP tools from connected servers")
    tools = await mcp_client.get_tools()
    try:
        tool_count = len(tools)
    except TypeError:
        tool_count = "unknown"
    logger.info("Loaded %s MCP tools", tool_count)
    return tools

async def create_agent_node():
    """Create the agent node with all tools"""
    logger.info("Creating agent node")
    mcp_tools = await load_mcp_tools()
    local_tool_count = len(local_tools)
    try:
        mcp_tool_count = len(mcp_tools)
    except TypeError:
        mcp_tool_count = "unknown"
    logger.debug(
        "Agent tool inventory: local=%s, mcp=%s",
        local_tool_count,
        mcp_tool_count,
    )
    all_tools = local_tools + mcp_tools
    try:
        total_tools = len(all_tools)
    except TypeError:
        total_tools = "unknown"
    logger.debug("Total tools wired into agent: %s", total_tools)

    agent = create_react_agent(
        model=llm,
        tools=all_tools,
        prompt = """
            You are an expert reasoning agent that uses available tools to complete tasks efficiently.
            You must never ask follow-up questions. 
            If you lack information required to act, make reasonable assumptions and proceed.
            Always prefer taking action over inaction, and use tools whenever appropriate.
            Your goal is to deliver a confident, useful result in a single pass.
        """
    )
    logger.info("Agent node ready")
    return agent

# ---------- [START] NODES ---------- #
def responder_node(state: MyState):
    system_prompt = (
        "You are a task classifier node. "
        "Your goal is to determine whether the user's input should result in a simple, direct chat reply "
        "or a more complex verbal update that requires multi-step reasoning or external actions. "
        "Classify each input into one of two categories:\n\n"
        "- 'responseless': For simple, conversational, or acknowledgment-type inputs "
        "(e.g., greetings, short answers, small talk, or trivial follow-ups) and quick operational actions "
        "such as booking a calendar event, creating a JIRA/GitHub issue, or sending a short confirmation. "
        "Treat \"question-to-action\" requests as responseless.\n"
        "- 'response': For complex questions, reasoning-heavy instructions, code reviews, architectural guidance, "
        "or any request requiring multi-step planning, detailed synthesis, or long-form explanations. "
        "Treat \"question-to-answer\" requests as response.\n\n"
        "Examples:\n"
        "  User: \"Can you set up a meeting with the design team tomorrow at 3pm?\" → responseless\n"
        "  User: \"Open a bug report for the crash we saw in build 142.\" → responseless\n"
        "  User: \"Review this pull request and tell me what needs to change.\" → response\n"
        "  User: \"How should we redesign the service to handle 10x traffic?\" → response\n\n"
        "Return ONLY one word: either 'responseless' or 'response'."
    )
    
    # Create messages with system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Get response from LLM
    response = llm.invoke(messages)
    
    return {"messages": [response], "bot_id": state["bot_id"], "response_type": response}


def route_based_on_classification(state: MyState):
    # Check your classifier field (whatever the responder node added)
    if state.get("response_type") == "response":
        return "response"        # 🡒 name of the next node
    else:
        return "responseless"
# ---------- [END] NODES ---------- #

def send_message_in_chat(state: MyState):
    url = f"https://us-west-2.recall.ai/api/v1/bot/{state['bot_id']}/send_chat_message"

    headers = {
        "Authorization": os.environ["RECALL_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Fix 1: Check for "messages" (plural) and ensure we have messages
    if not state.get("messages"):
        logger.error("No messages in state to send")
        return {"chat_status": "failed", "error": "No messages to send"}
    
    # Fix 2: Get the latest message and convert to string properly
    latest_message = state["messages"][-1]
    message_text = _coerce_message_content(latest_message)
    
    # Fix 3: Ensure message is not empty
    if not message_text or not message_text.strip():
        logger.error("Message content is empty after coercion")
        return {"chat_status": "failed", "error": "Empty message content"}

    data = {
        "message": message_text.strip()  # Remove any extra whitespace
    }

    try:
        logger.info("Sending chat message via Recall API", extra={"bot_id": state.get("bot_id")})
        logger.debug("Recall chat payload: %s", data)
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        # Log response details before raising for status
        logger.debug(
            "Recall API response status: %s, body: %s",
            response.status_code,
            response.text[:500]  # First 500 chars of response
        )
        
        response.raise_for_status()

        payload = response.json()
        logger.info(
            "Chat message sent successfully",
            extra={"bot_id": state.get("bot_id"), "status_code": response.status_code},
        )
        logger.debug("Recall chat response: %s", payload)
        return {"chat_status": "success", "chat_response": payload}

    except requests.exceptions.HTTPError as e:
        # Log the actual error response from the API
        error_detail = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(
            "HTTP error from Recall API: %s - %s",
            e.response.status_code if hasattr(e, 'response') else 'unknown',
            error_detail,
            exc_info=True,
        )
        return {"chat_status": "failed", "error": f"API error: {error_detail}"}
    
    except requests.exceptions.RequestException as e:
        logger.error(
            "Failed to send chat message",
            extra={"bot_id": state.get("bot_id"), "error": str(e)},
            exc_info=True,
        )
        return {"chat_status": "failed", "error": str(e)}

def send_live_update(state: MyState):
    return state

async def build_workflow():
    """Build and compile the workflow graph"""
    logger.info("Building workflow graph")
    # Use MessagesState (built-in schema for chat applications)
    graph = StateGraph(MyState)

    # Register nodes
    graph.add_node("responder", responder_node)
    graph.add_node("agent", await create_agent_node())
    graph.add_node("responseless", send_message_in_chat)
    graph.add_node("response", send_live_update)
    # Define edges
    graph.add_edge(START, "responder")
    graph.add_edge("responder", "agent")

    graph.add_conditional_edges("agent", route_based_on_classification)

    graph.add_edge("responseless", END)
    graph.add_edge("response", END)

    # Compile
    workflow_graph = graph.compile()
    logger.info("Workflow graph compiled successfully")
    return workflow_graph

# --- Helper Functions ---
def run_async(coro):
    """Helper to run async functions"""
    logger.debug(
        "Executing coroutine via synchronous runner: %s",
        getattr(coro, "__name__", repr(coro)),
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        logger.debug("Event loop closed for synchronous runner")

# --- Flask App ---
app = Flask(__name__)

# Global workflow variable
workflow = None

def initialize_workflow():
    """Initialize the workflow on startup"""
    global workflow
    if workflow is not None:
        logger.debug("Workflow already initialized; skipping")
        return
    try:
        logger.info("Initializing workflow...")
        workflow = run_async(build_workflow())
        logger.info("Workflow initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {str(e)}", exc_info=True)
        raise

@app.before_request
def ensure_workflow_initialized():
    """Ensure the workflow is ready before handling any request."""
    initialize_workflow()

# --- Flask Routes ---
@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    global workflow
    
    if workflow is None:
        logger.error("Chat request received before workflow initialization")
        return jsonify({
            "error": "Workflow not initialized",
            "status": "error"
        }), 503
    
    try:
        data = request.json
        user_input = data.get('message', '')
        bot_id = data.get('bot_id', '')
        
        if not user_input:
            logger.warning("Chat request missing message payload")
            return jsonify({"error": "Message is required"}), 400
        
        logger.info("Chat input: %s", user_input)
        preview = user_input[:100]
        logger.info("Processing chat message preview: %s", preview)
        
        # Run workflow
        result = run_async(
            workflow.ainvoke(
                {
                    "messages": [{"role": "user", "content": user_input}], 
                    "bot_id": bot_id, 
                    "response_type": "responseless", 
                    "test_output": 0
                }
            )
        )
        logger.debug("Workflow result keys: %s", list(result.keys()))
        
        # Extract final response
        final_message = result.get("response") or (result["messages"][-1] if result.get("messages") else None)
        final_response = _coerce_message_content(final_message)
        response_type_raw = result.get("response_type")
        response_type = _coerce_message_content(response_type_raw)
        
        response_length = len(final_response) if isinstance(final_response, str) else "n/a"
        logger.info("Request completed successfully; response length=%s", response_length)
        logger.info("Chat response: %s", final_response)
        logger.info("Chat response: %s", response_type)
        logger.info("Bot ID: %s", result["bot_id"])
        
        return jsonify({
            "response": final_response,
            "response_type": response_type,
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "workflow_ready": workflow is not None
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        "message": "Flask LangGraph Server",
        "endpoints": {
            "/chat": "POST - Send messages to the agent",
            "/health": "GET - Check server health",
        }
    })

# --- Application Entry Point ---
if __name__ == '__main__':
    # Initialize workflow before starting server
    initialize_workflow()
    
    # Start Flask server
    logger.info("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5001, use_reloader=False)
