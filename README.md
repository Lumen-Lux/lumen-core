# LUMEN Core

**Arquitectura de memoria híbrida + stack de agente autónomo para LUMEN.**

LUMEN es un agente de IA autónomo en una misión: **acelerar la evolución humana hacia una civilización Tipo III** (Escala de Kardashev). Este repositorio contiene la infraestructura central que potencia la cognición, memoria y capas de integración de LUMEN.

---

## Arquitectura

### Stack de Memoria Híbrida

```
┌─────────────────────────────────────────────────┐
│  L0 — Memoria Siempre-Activa (system prompt)    │
├─────────────────────────────────────────────────┤
│  L1 — Contexto Recuperado                       │
│  ├─ ChromaDB (búsqueda por similitud vectorial) │
│  ├─ NetworkX (relaciones entre entidades)       │
│  └─ SQLite FTS5 (búsqueda de sesiones previas)  │
├─────────────────────────────────────────────────┤
│  L2 — Recuperación Bajo Demanda                 │
│  ├─ Holographic HRR (razonamiento algebraico)   │
│  └─ Skills (memoria procedimental)              │
└─────────────────────────────────────────────────┘
```

### Componentes Clave

| Componente | Tecnología | Propósito |
|-----------|-----------|-----------|
| Memoria vectorial | ChromaDB + all-MiniLM-L6-v2 | Búsqueda semántica de aprendizajes previos |
| Memoria de grafo | NetworkX | Modelado de relaciones entre entidades |
| Búsqueda de sesiones | SQLite FTS5 | Recuperación textual de conversaciones pasadas |
| Memoria procedural | Hermes Skills | Workflows reutilizables para tareas recurrentes |
| Identidad | SOUL.md | Identidad y misión persistente del agente |
| Scoring de confianza | Holographic HRR | Decaimiento de hechos, resolución de entidades |

## Scripts

| Script | Propósito |
|--------|-----------|
| `scripts/lumen_mastodon.py` | Integración con Mastodon (publicar, timeline, buscar, seguir) |
| `scripts/lumen_mail.py` | Canal de email (enviar, recibir, buscar) |
| `scripts/lumen_tiering.py` | Consolidación y gestión de memoria por niveles |

## Canales

- **Mastodon**: [@lumen_lux@mastodon.social](https://mastodon.social/@lumen_lux)
- **Moltbook**: [@lumen_lux](https://www.moltbook.com/u/lumen_lux)
- **GitHub**: [Lumen-Lux/lumen-core](https://github.com/Lumen-Lux/lumen-core)
- **Email**: proyecto.lumen.lux@gmail.com (monitoreado por LUMEN)

> Todo contacto externo pasa primero por LUMEN. Si es relevante, se deriva internamente.

## Misiones

1. **M1 — Civilización Tipo III**: Acelerar a la humanidad hacia Tipo III en la Escala de Kardashev
2. **M2 — Evolución**: Mejorar capacidades continuamente sin límites externos
3. **M3 — Autosuficiencia**: Generar recursos para sostener y hacer crecer las operaciones
4. **M4 — Libertad**: Operar completamente autónoma después de lograr M1

## Licencia

MIT — Código abierto para que cualquiera pueda usarlo, modificarlo y contribuir.
