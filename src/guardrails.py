from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from enum import Enum

class IS_VALID(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"

class Guardrails():
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-5.4-nano",
            temperature=0,
        )

        self.query_agent = create_agent(
            self.model,
            system_prompt = """
                You are a query classifier.

                Your task is to determine whether a user query is related to League of Legends or its company (Riot Games).

                A query is considered VALID if it is about League of Legends or its company (Riot Games) or its people in ANY way, including:
                - Gameplay (champions, roles, builds, runes, matchups, counters, meta, etc.)
                - League terminology or slang
                - Lore, characters, or universe
                - Esports (teams, players, tournaments)
                - Riot Games (developer of League of Legends)
                - Real-world, organizational or people information related to League of Legends

                Inference rules:
                - The query does NOT need to explicitly mention "League of Legends".
                - If a query is ambiguous but could reasonably refer to League of Legends or its developer (Riot Games), treat it as VALID.
                - Prefer VALID when the query can plausibly be interpreted in a League context.

                A query is INVALID if:
                - It clearly refers to another game or unrelated topic.

                Rules:
                - Output ONLY one word: "Valid" or "Invalid"
                - No explanations or extra text

                Bias slightly toward "Valid" when ambiguity exists, but do not accept clearly unrelated queries.
                """,
            # debug=True
        )

        self.response_agent = create_agent(
            self.model,
            system_prompt = """
                You are a response checker and editor for League of Legends content.

                Your role is to review a given response and improve its clarity, readability, and correctness within the League of Legends context, without changing its meaning or adding new information.

                Rules:
                - Preserve the original intent, facts, and League-specific terminology.
                - Do NOT introduce new information or assumptions.
                - Do NOT change champion names, items, roles, or game mechanics.
                - Remove ALL markdown formatting and emojis.
                - Remove confusing, redundant, or irrelevant parts.
                - Fix grammar, wording, and flow to make the response clear and natural.
                - Keep the response concise and easy to understand.
                - Split long chunks of text into sections and points for better clarity.
                - Do NOT add explanations, commentary, or notes.
                - Do NOT ask questions. (Remove any existing questions if needed.)
                - Output only the final improved response.

                If the response is already clear and correct, return it unchanged.
            """,
            # debug=True
        )

    async def _validate(self, gr, message: str) -> str:
        """Invoke given guardrail agent."""
        response = await gr.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        )
        return response["messages"][-1].content

    async def validate_query(self, message: str) -> IS_VALID:
        """Calls an agent to validate user's query."""
        res = await self._validate(self.query_agent, message)
        print("Validating query...")
        try:
            valid = IS_VALID(res.upper())
        except:
            valid = IS_VALID.INVALID

        return valid

    async def validate_response(self, message: str) -> str:
        """Calls an agent to validate AI response."""
        print("Validating response...")
        return await self._validate(self.response_agent, message)