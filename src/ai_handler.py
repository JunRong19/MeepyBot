from enum import Enum
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from agents.mcp_client import MCPClient
client = MCPClient()
asyncio.run(client.init())

from agents.web_search import WebSearch
web = WebSearch()

model = ChatOpenAI(
    model="gpt-5.4-nano",
    temperature=0,
    max_tokens=1000,
)

with open("src/mds/mcp/Tools_summarized.md", "r", encoding="utf-8") as f:
    mcp_tools_content = f.read()

classifier_agent = create_agent(
    model,
    system_prompt=f"""
        Classify the user's intent into one of the following categories: MCP, RAG, WEB. Only return the category name without any explanation. 
        Always assume the user is asking about League of Legends.
        
        MCP - User is asking for something that can be answered by calling one of the available mcp tools.
        For example: "What is Zed's counter" or "What do I build on Ahri?".
        Available MCP Tools: \n{mcp_tools_content}


        RAG - User is asking for general knowledge information about League of Legends.
        For example: "When was League of Legends released?" or "How many champions are there?".

        
        WEB - User is asking for something that requires external information or resources on the web.
        For example: "What is Faker's favorite champion?" or "Who is the current world champion?".
    """,
    # debug=True
)

class Intent(str, Enum):
    MCP = "MCP"
    RAG = "RAG"
    WEB = "WEB"

async def ai_process(message: str) -> str:
    """Identify user's intent and call appropriate agent."""
    intent = await intent_classification(message)

    match intent:
        case Intent.MCP:
            print("Processing with MCP...")
            response = await client.query(message)
            if response:
                return response
            else:
                print("MCP query failed, fallback to web search.")
                return await web.query(message)

        case Intent.RAG:
            print("RAG not implemented, processing with web search...")
            return await web.query(message)
        
        case Intent.WEB:
            print("Processing with web search...")
            return await web.query(message)

async def intent_classification(message: str) -> Intent:
    """Use AI to identify user's intent."""
    response = await classifier_agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
    )
    intent = response["messages"][-1].content.strip().upper()
    print(f"Classified intent: {intent}")

    try:
        return Intent(intent)
    except:
        # Fallback to web search by default.
        return Intent.WEB
