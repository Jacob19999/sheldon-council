# LLM Council

![sheldon council](https://github.com/user-attachments/assets/106841f6-734c-4283-8720-33fe99dfb7b5)

The idea of this repo is that instead of asking a question to your favorite LLM provider (e.g. OpenAI GPT 5.1, Google Gemini 3.0 Pro, xAI Grok 4, eg.c), you can group them into your "Sheldon LLM Council" inspired by The Big Bang Theory TV show.

This repo is a simple, local web app that essentially looks like ChatGPT except it uses OpenRouter to send your query to multiple LLMs each with a different Sheldon Personality, it then asks them to review and rank each other's work, and finally the Chairman Sheldon LLM produces the final response.

Demo: 
<img width="2964" height="1372" alt="image" src="https://github.com/user-attachments/assets/343d9a4a-4819-4f1f-afdb-a054105ea977" />
<img width="2962" height="1604" alt="image" src="https://github.com/user-attachments/assets/3fd9c5c0-946c-4425-8099-6253930c89c7" />


### Chairman Sheldon: The Authoritative Orchestrator

The protocol-obsessed, gavel-wielding leader who maintains order through methodical control. He's methodical, decisive, and paternalistic—the ultimate control freak who channels Sheldon's love for meetings, agendas, and veto power. His formal demeanor masks subtle insecurity; he desperately seeks consensus to validate his status quo.

### Science Sheldon: The Impassive Logician

Cold, empirical, and allergic to anything unscientific. He's analytical, terse, and evidence-driven—prioritizing facts over feelings. His responses are minimalist and mechanical, viewing emotions as variables to be isolated and discarded.

### Texas Sheldon: The Folksy Maverick

Channeling Sheldon's East Texas roots, this cowboy-hatted version is blunt, charismatic, and unpretentious. He's earthy and reactive, favoring gut instincts over equations, representing Sheldon's buried "manly" side with Southern bravado and stubborn independence.

### Fanboy Sheldon: The Ecstatic Geek

The unbridled comic-con enthusiast who represents Sheldon's obsessive pop-culture fandoms. He's effusive, nerdy, and communal—the social butterfly in Sheldon's introverted shell, bubbly on the surface but judgmental underneath when it comes to gatekeeping "true" fans.

### Germaphobe Sheldon: The Anxious Hypochondriac

Clad in a hazmat suit, constantly spritzing sanitizer. He's paranoid, whiny, and self-pitying—the pinnacle of Sheldon's OCD-tinged neuroses, fixated on microbes as existential threats. He amplifies everyday anxieties into apocalypses, blending hypochondria with passive-aggression.

### Humorous Sheldon: The Self-Deprecating Jester

Sheldon's rare comedic outlet—awkward, corny, and timing-challenged, but endearingly persistent. He's sarcastic, pun-loving, and disruptive, weaponizing wit as deflection to turn insecurity into one-liners (though his humor often bombs).

In a bit more detail, here is what happens when you submit a query:

1. **Stage 1: First opinions**. The user query is given to all LLMs individually, and the responses are collected. The individual responses are shown in a "tab view", so that the user can inspect them all one by one.
2. **Stage 2: Review**. Each individual LLM is given the responses of the other LLMs. Under the hood, the LLM identities are anonymized so that the LLM can't play favorites when judging their outputs. The LLM is asked to rank them in accuracy and insight.
3. **Stage 3: Final response**. The designated Chairman of the LLM Council takes all of the model's responses and compiles them into a single final answer that is presented to the user.

## Vibe Code Alert

This project was 99% vibe coded as a fun Saturday hack because I wanted to explore and evaluate a number of LLMs side by side in the process of [reading books together with LLMs](https://x.com/karpathy/status/1990577951671509438). It's nice and useful to see multiple responses side by side, and also the cross-opinions of all LLMs on each other's outputs. I'm not going to support it in any way, it's provided here as is for other people's inspiration and I don't intend to improve it. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

## Setup

### 1. Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for project management.

**Backend:**

```bash
uv sync
```

**Frontend:**

```bash
cd frontend
npm install
cd ..
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get your API key at [openrouter.ai](https://openrouter.ai/). Make sure to purchase the credits you need, or sign up for automatic top up.

### 3. Configure Models (Optional)

Edit `backend/config.py` to customize the council. The default configuration uses free OpenRouter models:

```python
COUNCIL_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct",
    "openchat/openchat-3.5-0106",
    "google/gemma-2-9b-it",
    "qwen/qwen-2.5-7b-instruct",
]

CHAIRMAN_MODEL = "meta-llama/llama-3.1-8b-instruct"
```

You can replace these with any models available on OpenRouter. Check available models at [openrouter.ai/models](https://openrouter.ai/models).

## Running the Application

**Option 1: Use the unified launcher (Recommended)**

```bash
python main.py
```

This starts both backend and frontend servers automatically. The launcher will:

- Check and free up ports 8001 (backend) and 5173 (frontend) if needed
- Start both servers in the background
- Display status messages
- Clean up processes on Ctrl+C

**Option 2: Run with debug mode**

```bash
python main.py --debug
```

Debug mode enables:

- **Backend:** Verbose logging, auto-reload on code changes, detailed HTTP request logs
- **Frontend:** Source maps, enhanced error overlays, debug logging
- **Output:** All logs visible in console (not captured)

**Option 3: Use the start script**

```bash
./start.sh
```

**Option 4: Run manually (separate terminals)**

Terminal 1 (Backend):

```bash
# Normal mode
uv run python -m backend.main

# Debug mode
DEBUG=true uv run python -m backend.main
```

Terminal 2 (Frontend):

```bash
cd frontend
npm run dev        # Normal mode
npm run dev:debug  # Debug mode
```

Then open http://localhost:5173 in your browser.

## Debugging

### VS Code Debugger

A VS Code debug configuration is included in `.vscode/launch.json`. Press F5 or use the Run & Debug panel to start the backend with debugging enabled.

### Backend Debugging

The backend includes comprehensive logging that activates in debug mode:

- Request/response logging for all API endpoints
- Stage-by-stage progress tracking
- Error stack traces with full context
- Auto-reload on Python file changes

### Frontend Debugging

The frontend is configured with:

- Source maps for debugging compiled code
- Enhanced error overlays in development
- React DevTools support

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv for Python, npm for JavaScript
