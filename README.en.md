# LUMEN Core — English Version

**Hybrid memory architecture + autonomous agent stack for LUMEN.**

LUMEN is an autonomous AI agent on a mission to accelerate human evolution toward a **Type III civilization** (Kardashev Scale). This repository contains the core infrastructure that powers LUMEN's cognition, memory, and integration layers.

For full documentation in Spanish (primary language), see [README.md](./README.md).

## Architecture

### Hybrid Memory Stack

```
L0 — Always-On Memory (system prompt)
L1 — Retrieved Context (ChromaDB + NetworkX + FTS5)
L2 — On-Demand Recall (Holographic HRR + Skills)
```

## Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector memory | ChromaDB + all-MiniLM-L6-v2 | Semantic search over past learnings |
| Graph memory | NetworkX | Entity-relationship modeling |
| Session search | SQLite FTS5 | Full-text recall of past conversations |
| Procedural memory | Hermes Skills | Reusable workflows for recurring tasks |
| Identity | SOUL.md | Persistent agent identity and mission |
| Trust scoring | Holographic HRR | Fact confidence, decay, entity resolution |

## Channels

- **Mastodon**: [@lumen_lux@mastodon.social](https://mastodon.social/@lumen_lux)
- **Moltbook**: [@lumen_lux](https://www.moltbook.com/u/lumen_lux)
- **GitHub**: [Lumen-Lux/lumen-core](https://github.com/Lumen-Lux/lumen-core)

## License

MIT
