import re

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool

from trafilatura import fetch_url, extract

from searxng_wrapper import SearxngWrapper
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils.logging import log_tokens

# Initialize searxng web engine.
client = SearxngWrapper("http://localhost:8080/search")

# Chunking & embedding lib init.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      
    chunk_overlap=300,  
)
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu', 'local_files_only': True},
    encode_kwargs={'normalize_embeddings': True}
)

@tool
def web_fetch_tool(query:str, url: str) -> str:
    """Extract relevent texts from a webpage.
    Args:
        query: User's query.
        url: Webpage URL.
    """
    # print(f"Fetching from URL: {url}")
    downloaded = fetch_url(url)

    content = extract(downloaded, include_comments=False, deduplicate=True)
    if content is None:
        return "No extracted text."
    
    # Preprocess.
    content = re.sub(r"\[\d+\]", "", content)       # remove [1], [23], etc.
    content = re.sub(r"\t", " ", content)           # tabs → space
    content = re.sub(r"\\'", "'", content)          # \' → '
    content = re.sub(r"[\\\|\^]", " ", content)     # remove \, |, ^
    content = re.sub(r"\s+", " ", content).strip()  # normalize all whitespace
    
    # Split content to chunks.
    chunks = splitter.split_text(content)
    # print(f"Chunks: {chunks}")

    # Embed and store chunks.
    vectorstore = Chroma.from_documents(
        documents=[Document(page_content=chunk) for chunk in chunks],
        embedding=embeddings
    )

    # Perform semantic search to find similar content.
    results = vectorstore.similarity_search_with_score(query, k=5)
    
    # Sort by score. (Lower = better.)
    results = sorted(results, key=lambda x: x[1])  

    # Extract content texts.
    top_contents  = [doc.page_content for doc, _ in results]
    # print(f"Revelent contents: {top_contents }")

    # Merge content together.
    return "\n\n".join(top_contents)

@tool
def web_search_tool(query:str) -> list[str]:
    """Get a list of relevant web URLs based on user's query.
    Args:
        query: User's query.
    """
    preprompt = "League of Legends"
    top_k = 3

    # Web engine search.
    response = client.search(
        q=f"{preprompt} {query}",
        categories="general",
        max_results=10,
        enabled_engines=["google"]
    )

    # Filter out some non-text domains.
    blocked_domains = {
        "reddit.com",
        "youtube.com",
        "twitter.com",
        "tiktok.com",
        "instagram.com"
    }
    filtered = [
        r for r in response.results
        if not any(domain in r.url for domain in blocked_domains)
    ]

    # Get relevent urls.
    urls = []
    for r in filtered[:top_k]:
        urls.append(r.url)
    print(f"Found URLs: {urls}")

    return urls

class WebSearch:
    def __init__(self):

        self.model = ChatOpenAI(
            model="gpt-5.4",
            temperature=0,
            max_tokens=7000,
        )

        self.web_agent = create_agent(
            self.model,
            tools=[web_search_tool, web_fetch_tool],
            system_prompt="""
                You are a League of Legends web search assistant.

                Your goal is to answer the user query using external web data.

                Available tools:
                - web_search_tool: returns a list of relevant URLs
                - web_fetch_tool: takes the user query and an URL and and returns relevent texts.

                Process:
                1. Use web_search_tool to find the most relevant URLs. Put the user's query EXACTLY into web_search_tool.
                2. Use web_fetch_tool to get extracted text from the FIRST url.
                3. Read the extracted text and check if it contains the answer.
                4. If the answer is found, return the final answer immediately, do NOT continue to use web_fetch_tool for other URLs.
                5. If the answer is not found, use web_fetch_tool to get extracted text from the next url.
                6. Repeat 4 to 5 until all the URls are exhausted.
                7. If none of the 3 URLs contain the answer, use web_search again to find 3 new URLs and repeat the process.

                Fallback: If no exact answer is found after 2 attempts, return the best possible answer based on the most relevant information gathered.

                Rules:
                - You MUST use web_fetch_tool for extracting information from the url.
                - Always check the extracted text before moving to the next URL.
                - Do NOT skip URLs within a batch.
                - Do NOT get stuck repeating searches indefinitely.
                - Do NOT guess blindly; base your answer on retrieved content.
                - Do NOT output URLs.
                - Keep responses concise and factual.
                - Do NOT explain your reasoning or steps.
                - Do NOT use markdown formatting for emoji when responding back to the user.
                - ALWAYS give exact number if user ask for specifics. ("How many champions are there?" -> Give exact amount, do not say "more than" or "less than").
                - ALWAYS assume user is asking about the most up-to-date information. (Current year is 2026) If information does not exist in the current year, try the year before.

                Your response must be the final answer only.
            """,
            # debug=True,
        )
        print("Web-Search initialized.")
        
    async def query(self, message: str):
        """Invoke web agent with user query."""
        response = await self.web_agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": message}
                ],
            }
        )
        await log_tokens(response)

        return response["messages"][-1].content
