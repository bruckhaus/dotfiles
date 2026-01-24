# Perplexity RAG CLI

True retrieval-augmented generation combining your local knowledge base with Perplexity AI.

## Setup
1. Install pplx-cli: `uv tool install pplx-cli`
2. Set API key: Add `PERPLEXITY_API_KEY="pplx-key"` to `~/.env.local`
3. Build your KB: Use `pr` to automatically save interactions

## Usage

```bash
# True RAG: searches local KB, sends context to Perplexity
pr "what's my name?"

# Pure Perplexity (no KB influence)
pn "latest news about AI"

# Local KB only (no API call)  
pk "personal information"

# Interactive chat
pplxc

# Force Perplexity only (skip local search)
pr --force-perplexity "quantum computing"

# Don't save to KB
pr --no-save "temporary question"
```

## Behavior

- **`pr`** (RAG): Local KB → Perplexity API → Save to KB
- **`pn`** (Pure): Direct Perplexity API, no saving
- **`pk`** (Local): Search your notes only
- **`pplxc`** (Chat): Interactive mode

## Tech Stack

- **Local RAG**: BGE embeddings + SQLite vector search
- **API Integration**: Context-augmented Perplexity queries
- **Auto-save**: Every interaction becomes future context

Build your personal knowledge base over time for increasingly personalized AI responses!