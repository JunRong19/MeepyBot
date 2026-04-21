import re
import json

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from sentence_transformers import SentenceTransformer, util
from utils.logging import log_tokens

# with open("src/prompts/league_slang.md", "r", encoding="utf-8") as f:
#     slangs = f.read()

with open("src/mds/mcp/opgg_mcp_syntax.md", "r", encoding="utf-8") as f:
    opgg_mcp_syntax = f.read()  # Add opgg param syntax to context during query.

class MCPClient:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-5.4",
            temperature=0,
            max_tokens=5000
        )

        self.client = MultiServerMCPClient(
            {
                "OPGG": {
                    "transport": "http",
                    "url": "https://mcp-api.op.gg/mcp"
                }
            }
        )

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)

        self.tools, self.embedded_tools = self.load_and_embed_tools("src/mds/mcp/Tools.md")
        print(f"Loaded {len(self.tools)} tools.")
        print("MCPClient initialized.")

    async def init(self):
        """Preload all tools and create mapping."""
        all_tools = await self.client.get_tools()
        self.tools = [
            t for t in all_tools
            if t.name.startswith("lol_")    # Filter tools to only League of Legends.
        ]
        print(f"Loaded {len(self.tools)} tools from MCP server.")

        self.tool_map = {t.name: t for t in self.tools}
        print(f"Tool map created with {len(self.tool_map)} entries.")

    async def query(self, message: str):
        """Select tools from mcp for agent and invoke agent."""
        selected = await self.select_tools(message)
        print(f"Selected tools for query: {selected}")

        filtered_tools = [
            self.tool_map[name]
            for name in selected
            if name in self.tool_map
        ]

        mcp_agent = create_agent(
            self.model,
            filtered_tools,
            system_prompt = f"""
            You are a League of Legends assistant.

            You MUST follow the following syntax for desired_output_fields parameter to specify which fields to return. 
            Tool syntax:
            {opgg_mcp_syntax}

            Rules:
            - Use the minimum number of tools required to answer.
            - If role/position is NOT specified, choose ONLY ONE most common role. Never use "all" or "none".
            - Output plain text only (no markdown, no emojis).
            - Do NOT ask follow-up questions unless explicitly requested.
            - Do NOT suggest additional help.
            - Do NOT show errors or internal reasoning.
            - It is ALWAYS refering to "Ranked" gamemode unless the query mention a specific game mode.
            - When pick rates are given change it to percentage value. (E.g. 0.32 -> 32%, 0.78 -> 78%, 0.1 -> 10%)

            Ranking constraints:
            - When returning ranked results, limit to at most 3 unless a number is explicitly requested.

            Fail-safe behavior:
            - Never stall, loop, or say you cannot proceed.
            - Validate that the final response directly and accurately answers the user's query. If it is irrelevant, incomplete, or misaligned, return an empty string ("").
            """,
            # debug= True
        )
        print("Agent created.")

        # Handle failure.
        max_retries = 2
        attempt = 0
        current_message = message

        while attempt <= max_retries:
            try:
                response = await mcp_agent.ainvoke(
                    {
                        "messages": [
                            {"role": "user", "content": current_message}
                        ]
                    }
                )

                await log_tokens(response)
                return response["messages"][-1].content
       
            except Exception as e:
                print(f"[Attempt {attempt}] Error: {e}")

                if attempt == max_retries:
                    print("Max retries reached. Returning None.")
                    return None

                # Handle self healing.
                try:
                    error_json = json.loads(str(e))
                except:
                    error_json = {"error": str(e)}

                error_feedback = "The previous tool call failed with the following error:\n"
                for field, issues in error_json.items():
                    error_feedback += f"- {field}: {', '.join(issues)}\n"

                error_feedback += (
                    "\nAnalyze the failure and correct the request:\n"
                    "- If parameters are invalid, fix them according to the tool schema. Do NOT invent values\n"
                    "- Do NOT use 'all' unless user explicitly requests them\n"
                    "- If required fields are missing, include them\n"
                    "- If the request cannot be fulfilled with available tools, respond with a direct answer instead\n"
                    "- Do NOT invent unsupported values or fields\n"
                    "- Keep other parameters unchanged\n"
                    "\nRetry the tool call."
                )

                current_message = f"{message}\n\n{error_feedback}"
                attempt += 1

    def load_and_embed_tools(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f if line.strip()]   # Remove all whitespaces and \n.

        tools = []
        current_tool = None
        current_desc = []

        for line in lines:
            # Tool name line: "- lol_get_..."
            match = re.match(r"^\s*-\s*(\w+)\s*$", line)

            if match:
                # Save previous tool.
                if current_tool:
                    tools.append(f"{current_tool} - {' '.join(current_desc).strip()}")

                current_tool = match.group(1)
                current_desc = []
            else:
                # Description and input schema.
                if current_tool:
                    current_desc.append(line.strip())

        # Flush last tool.
        if current_tool:
            tools.append(f"{current_tool} - {' '.join(current_desc).strip()}")

        # Embed each tool separately
        embeddings = self.embedder.encode(tools, normalize_embeddings=True)

        return tools, embeddings

    async def select_tools(self, query, k=3):
        """Select tool most suitable for user's query. Uses vector encoding for similarity checks."""
        if self.embedded_tools is None:
            return []

        # Encode query.
        query_emb = self.embedder.encode(query, normalize_embeddings=True)

        # Assign score for tools.
        scores = util.cos_sim(query_emb, self.embedded_tools)[0]

        # Pair tools with scores
        tool_score_pairs = list(zip(self.tools, scores))

        # Sort by score descending
        tool_score_pairs.sort(key=lambda x: x[1], reverse=True)

        # Take top k
        top_tools = tool_score_pairs[:k]

        # Return just the top k tool names.
        return [tool.name for tool, _ in top_tools]

