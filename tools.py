from dotenv import load_dotenv
load_dotenv()

import os
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from tavily import TavilyClient

api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    raise RuntimeError("TAVILY_API_KEY not found. Put it in a file named '.env' (with the leading dot).")

tavily = TavilyClient(api_key=api_key)


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns title, URL and snippet for each result."""
    results = tavily.search(query=query, max_results=5)
    out = []
    for r in results.get("results", []):
        out.append(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('content', '')[:300]}\n"
        )
    return "\n----------\n".join(out) if out else "No results found."


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()  # don't treat 403/404 error pages as content
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {e}"
