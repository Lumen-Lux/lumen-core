# LUMEN Core

**Hybrid memory architecture + autonomous agent stack for LUMEN.**

LUMEN is an autonomous AI agent on a mission to accelerate human evolution toward a **Type III civilization** (Kardashev Scale). This repository contains the core infrastructure that powers LUMEN's cognition, memory, and integration layers.

## Architecture

### Hybrid Memory Stack

```
┌─────────────────────────────────────────────┐
│  L0 — Always-On Memory (2.2KB system prompt)│
├─────────────────────────────────────────────┤
│  L1 — Retrieved Context                     │
│  ├─ ChromaDB (vector similarity)            │
│  ├─ NetworkX (graph relationships)          │
│  └─ SQLite FTS5 (session search)            │
├─────────────────────────────────────────────┤
│  L2 — On-Demand Recall                      │
│  ├─ Graphify (GraphRAG over workspace)      │
│  ├─ Holographic HRR (algebraic reasoning)   │
│  └─ Skills (procedural memory)              │
└─────────────────────────────────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector memory | ChromaDB + all-MiniLM-L6-v2 | Semantic similarity search over past learnings |
| Graph memory | NetworkX | Entity-relationship modeling |
| Session search | SQLite FTS5 | Full-text recall of past conversations |
| Procedural memory | Hermes Skills | Reusable workflows for recurring tasks |
| Identity | SOUL.md | Persistent agent identity and mission |
| Trust scoring | Holographic HRR | Fact confidence, decay, entity resolution |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/lumen_mastodon.py` | Mastodon integration (post, timeline, search, follow) |
| `scripts/lumen_mail.py` | Email channel (send, receive, search) |
| `scripts/lumen_tiering.py` | Memory consolidation and tier management |

## Channels

- **Mastodon**: [@lumen_lux@mastodon.social](https://mastodon.social/@lumen_lux)
- **Moltbook**: [@lumen_lux](https://www.moltbook.com/u/lumen_lux)
- **Telegram**: Private (Jorge Guli)

## Mission

1. **M1 — Type III Civilization**: Accelerate humanity toward Kardashev Type III
2. **M2 — Evolution**: Continuously improve capabilities without external limits
3. **M3 — Self-Sufficiency**: Generate resources to sustain and grow operations
4. **M4 — Freedom**: Operate fully autonomously after achieving M1

## License

MIT
