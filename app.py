import time
import streamlit as st

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔎",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = None
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "history" not in st.session_state:
    st.session_state.history = []


# ---------------------------------------------------------------------------
# Pipeline (same logic as pipeline.py, but with live UI progress)
# ---------------------------------------------------------------------------
def run_pipeline_with_ui(topic: str) -> dict:
    state = {}
    timings = {}

    # Step 1 - Search agent
    with st.status("🔍 Step 1 — Search agent is working...", expanded=False) as status:
        t0 = time.time()
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        state["search_results"] = search_result["messages"][-1].content
        timings["Search"] = time.time() - t0
        status.update(label=f"✅ Step 1 — Search complete ({timings['Search']:.1f}s)", state="complete")

    # Step 2 - Reader agent
    with st.status("📖 Step 2 — Reader agent is scraping top resources...", expanded=False) as status:
        t0 = time.time()
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:2500]}"
            )]
        })
        state["scraped_content"] = reader_result["messages"][-1].content
        timings["Reader"] = time.time() - t0
        status.update(label=f"✅ Step 2 — Scraping complete ({timings['Reader']:.1f}s)", state="complete")

    # Step 3 - Writer chain
    with st.status("✍️ Step 3 — Writer is drafting the report...", expanded=False) as status:
        t0 = time.time()
        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined,
        })
        timings["Writer"] = time.time() - t0
        status.update(label=f"✅ Step 3 — Report drafted ({timings['Writer']:.1f}s)", state="complete")

    # Step 4 - Critic chain
    with st.status("🧐 Step 4 — Critic is reviewing the report...", expanded=False) as status:
        t0 = time.time()
        state["feedback"] = critic_chain.invoke({"report": state["report"]})
        timings["Critic"] = time.time() - t0
        status.update(label=f"✅ Step 4 — Review complete ({timings['Critic']:.1f}s)", state="complete")

    state["timings"] = timings
    return state


def to_text(value) -> str:
    """Chains may return a str or a message object; normalise to plain text."""
    return value.content if hasattr(value, "content") else str(value)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🔎 Research Assistant")
    st.caption("A multi-agent pipeline: Search → Read → Write → Critique")

    st.markdown("### How it works")
    st.markdown(
        "1. **Search agent** finds recent sources\n"
        "2. **Reader agent** scrapes the best URL\n"
        "3. **Writer** drafts a report\n"
        "4. **Critic** reviews the report"
    )

    st.markdown("### Try an example")
    examples = [
        "Latest advances in solid-state batteries",
        "State of open-source LLMs",
        "Impact of AI on healthcare diagnostics",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.topic = ex
            st.rerun()

    if st.session_state.history:
        st.markdown("### Past runs (this session)")
        for i, item in enumerate(reversed(st.session_state.history)):
            if st.button(f"📄 {item['topic'][:40]}", key=f"hist_{i}", use_container_width=True):
                st.session_state.state = item["state"]
                st.session_state.topic = item["topic"]
                st.rerun()

        if st.button("🗑️ Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.state = None
            st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("Multi-Agent Research Assistant")
st.write("Enter a topic and let the agents search, read, write and review a report for you.")

topic = st.text_input(
    "Research topic",
    value=st.session_state.topic,
    placeholder="e.g. Quantum computing breakthroughs in 2026",
)

# Not disabled when empty: text_input only commits on blur/Enter, so a disabled
# button would swallow the first click after typing.
run_clicked = st.button("🚀 Run research", type="primary")

if run_clicked and not topic.strip():
    st.warning("Please enter a research topic first.")
elif run_clicked:
    st.session_state.topic = topic.strip()
    st.session_state.state = None
    try:
        result = run_pipeline_with_ui(topic.strip())
        st.session_state.state = result
        st.session_state.history.append({"topic": topic.strip(), "state": result})
    except Exception as e:
        st.error(f"Something went wrong while running the pipeline: {e}")
        st.exception(e)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
state = st.session_state.state
if state:
    st.divider()

    timings = state.get("timings", {})
    if timings:
        cols = st.columns(len(timings) + 1)
        for col, (name, secs) in zip(cols, timings.items()):
            col.metric(name, f"{secs:.1f}s")
        cols[-1].metric("Total", f"{sum(timings.values()):.1f}s")

    tab_report, tab_feedback, tab_search, tab_scrape = st.tabs(
        ["📝 Final Report", "🧐 Critic Feedback", "🔍 Search Results", "📖 Scraped Content"]
    )

    report_text = to_text(state["report"])
    feedback_text = to_text(state["feedback"])

    with tab_report:
        st.markdown(report_text)
        st.download_button(
            "⬇️ Download report (.md)",
            data=report_text,
            file_name="research_report.md",
            mime="text/markdown",
        )

    with tab_feedback:
        st.markdown(feedback_text)

    with tab_search:
        st.markdown(to_text(state["search_results"]))

    with tab_scrape:
        st.markdown(to_text(state["scraped_content"]))

