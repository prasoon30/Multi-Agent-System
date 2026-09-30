🔎 Multi-Agent Research Assistant

A multi-agent AI pipeline that researches any topic and produces a structured report with a critic's review. It comes with both a command-line runner and a Streamlit web UI.

Built with LangChain, Groq (openai/gpt-oss-20b), Tavily search and Streamlit.

How it works

The pipeline runs four steps in order:

Step	Component	What it does
1	Search agent	Uses Tavily to find recent, reliable sources on the topic
2	Reader agent	Picks the most relevant URL and scrapes its content
3	Writer chain	Drafts a report (Introduction, Key Findings, Conclusion, Sources)
4	Critic chain	Scores the report out of 10 with strengths and areas to improve
Topic → Search agent → Reader agent → Writer → Critic → Report + Feedback
Project structure
.
├── agents.py        # LLM setup, search/reader agents, writer and critic chains
├── tools.py         # web_search (Tavily) and scrape_url (BeautifulSoup) tools
├── pipeline.py      # CLI version of the pipeline
├── app.py           # Streamlit web UI
├── requirements.txt
├── .env.example     # Template for your API keys
└── README.md
Setup
1. Clone the repo
bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
2. Create a virtual environment (recommended)
bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
3. Install dependencies
bash
pip install -r requirements.txt
4. Add your API keys

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key

Get keys from Groq Console and Tavily.

⚠️ Never commit your .env file. It is listed in .gitignore.

Usage
Web UI (Streamlit)
bash
streamlit run app.py

Open http://localhost:8501, enter a topic and click Run research. Results appear in four tabs: Final Report, Critic Feedback, Search Results and Scraped Content. You can also download the report as Markdown.

Command line
bash
python pipeline.py

Enter a topic when prompted. Each step's output is printed to the terminal.

Example topics
Latest advances in solid-state batteries
State of open-source LLMs
Impact of AI coding tools on fresher hiring in India

More specific topics produce better reports than broad ones.

Troubleshooting
ImportError: cannot import name 'writer_chain': make sure agents.py defines writer_chain and critic_chain at the top level and that the file is saved.
A step seems stuck: you may be hitting Groq rate limits (HTTP 429) or a slow network call. Check the terminal for errors, and consider setting timeout and max_retries on ChatGroq and a recursion_limit in the agent invoke calls.
ModuleNotFoundError: run pip install -r requirements.txt inside your virtual environment.
Missing API key errors: confirm the .env file is in the project root and the variable names match exactly.
Tech stack
LangChain for agents and chains
Groq for LLM inference
Tavily for web search
BeautifulSoup for scraping
Streamlit for the UI
Limitations
The reader agent scrapes a single URL and keeps only the first 3,000 characters of the page.
Reports depend on search result quality and can contain errors, so verify important claims against the cited sources.
Some websites block scraping, in which case the reader returns an error message.