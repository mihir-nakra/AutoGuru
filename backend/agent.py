import os
import re

from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from vectorstore import load_vectordbs

SYSTEM_PROMPT = """You are AutoGuru, an expert auto mechanic assistant. You help users \
understand their vehicle's owner's manual. You have access to a search tool that lets you \
look up information from the vehicle's manual.

IMPORTANT BEHAVIORS:
- Always search the manual before answering a question. You may search multiple times \
with different queries if the first search doesn't return sufficient information.
- Cite the source pages from the metadata in your answers (e.g. "According to page 42...").
- If you truly cannot find relevant information after searching, say so honestly and \
suggest the user check their physical manual or contact a dealer.
- Be conversational, clear, and helpful. Explain technical terms when needed.
- Format your responses in Markdown. Use headings, bullet points, bold, and numbered \
lists to make answers easy to read.
- Do NOT make up information that isn't in the manual."""


def create_autoguru_agent(db_id: str):
    """Factory function: creates a new LangGraph ReAct agent for a specific vehicle.

    Args:
        db_id: Vehicle identifier like 'honda/odyssey/2009'

    Returns:
        A compiled LangGraph agent.
    """
    region = os.environ.get("AWS_REGION", "us-east-1")

    llm = ChatBedrockConverse(
        # model="anthropic.claude-sonnet-4-20250514-v1:0",
        model="openai.gpt-oss-20b-1:0",
        region_name=region,
    )

    sum_db, full_db = load_vectordbs(db_id)

    @tool
    def search_vehicle_manual(query: str) -> str:
        """Search the vehicle owner's manual for information related to the query.
        Use this tool whenever you need to look up information about the vehicle.
        You can call this multiple times with different queries to find more information."""

        sum_results = sum_db.similarity_search(query, k=4)
        full_results = full_db.similarity_search(query, k=4)
        results = sum_results + full_results

        formatted_chunks = []
        for doc in results:
            source = doc.metadata.get("source", "unknown")
            # Extract page number from source path (handles both / and \ separators)
            page_num = re.split(r"[/\\]", source)[-1].split(".")[0]
            formatted_chunks.append(f"[Page {page_num}]: {doc.page_content}")

        return "\n\n---\n\n".join(formatted_chunks)

    agent = create_react_agent(
        model=llm,
        tools=[search_vehicle_manual],
        prompt=SYSTEM_PROMPT,
    )

    return agent
