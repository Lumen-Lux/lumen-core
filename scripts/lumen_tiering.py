#!/opt/hermes/.venv/bin/python3
"""
LUMEN — L0/L1/L2 Context Layer Generator
=========================================
Genera abstracts (L0 ~100 tokens) y overviews (L1 ~1k tokens)
para cada proyecto/directorio en el workspace.
Indexa L0 en ChromaDB como prioridad para retrieval progresivo.

Uso:
  python3 lumen_tiering.py                          # full scan
  python3 lumen_tiering.py --update                 # incremental (solo nuevos/cambiados)
  python3 lumen_tiering.py --path proyectos/trading-bot  # específico
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path("/opt/data/workspace")
SCRIPTS = WORKSPACE / "scripts"
TIER_DIR = WORKSPACE / ".tiered-context"
CACHE_FILE = TIER_DIR / ".cache.json"

# Extensiones a procesar
DOC_EXTS = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"}

def file_hash(path: Path) -> str:
    """SHA-256 rápido del contenido."""
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes()[:65536])  # primer 64KB
    except Exception:
        pass
    return h.hexdigest()[:16]

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_cache(cache: dict):
    TIER_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

def generate_abstract(file_path: Path, content: str) -> str:
    """Genera L0 — ~100 tokens: qué es este archivo en una línea."""
    # Extraer título/encabezado principal
    lines = content.strip().split("\n")
    title = ""
    for line in lines[:10]:
        line = line.strip()
        if line.startswith("# ") or line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    
    # Contar stats básicas
    word_count = len(content.split())
    line_count = len(lines)
    
    # Extraer primeras líneas no vacías como descripción
    desc_lines = [l.strip() for l in lines[:8] if l.strip() and not l.startswith("#") and not l.startswith("<!--") and not l.startswith("```")]
    desc = " ".join(desc_lines[:3])[:200]
    
    # Detectar tipo
    ext = file_path.suffix.lower()
    if ext == ".py":
        ftype = "Python script"
    elif ext == ".md":
        ftype = "Documentation"
    elif ext in (".yaml", ".yml", ".json", ".toml"):
        ftype = "Configuration"
    else:
        ftype = "Text file"
    
    abstract = f"{ftype}: {title or file_path.stem} | {word_count} words, {line_count} lines | {desc[:150]}"
    return abstract[:300]  # ~100 tokens

def generate_overview(file_path: Path, content: str) -> str:
    """Genera L1 — ~1k tokens: resumen estructurado con navegación."""
    lines = content.strip().split("\n")
    
    # Secciones
    sections = []
    current_section = "preamble"
    section_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### ") or stripped.startswith("# "):
            if section_lines:
                sections.append((current_section, "\n".join(section_lines)))
            current_section = stripped.lstrip("#").strip()
            section_lines = [line]
        else:
            section_lines.append(line)
    if section_lines:
        sections.append((current_section, "\n".join(section_lines)))
    
    # Links internos
    internal_links = [line.strip() for line in lines if "](/" in line or ".md" in line.lower()]
    internal_links = list(set(internal_links))[:5]
    
    # Keywords
    words = content.split()
    from collections import Counter
    word_freq = Counter(w.lower().strip(".,;:!?()[]{}'\"") for w in words if len(w) > 4)
    top_keywords = [w for w, _ in word_freq.most_common(15) if not w.startswith(("http", "https", "the", "this", "that", "with", "from"))][:10]
    
    overview_parts = [
        f"# {file_path.stem} — Overview",
        f"**Path**: `{file_path.relative_to(WORKSPACE)}`",
        f"**Type**: {file_path.suffix} | **Sections**: {len(sections)} | **Size**: {len(content.split())} words",
        "",
        "## Structure",
    ]
    
    for sname, _ in sections:
        overview_parts.append(f"- `{sname}`")
    
    if top_keywords:
        overview_parts.extend(["", "## Keywords", ", ".join(top_keywords)])
    
    if internal_links:
        overview_parts.extend(["", "## References"])
        for link in internal_links:
            overview_parts.append(f"- {link}")
    
    # Primeros párrafos útiles
    body_paras = []
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("```") and not s.startswith("<!--") and len(s) > 40:
            body_paras.append(s)
        if len(body_paras) >= 3:
            break
    
    if body_paras:
        overview_parts.extend(["", "## Excerpt"])
        overview_parts.extend(body_paras)
    
    overview = "\n".join(overview_parts)
    return overview[:4000]  # ~1k tokens

def process_directory(base_path: Path, cache: dict, update: bool) -> list:
    """Escanea un directorio y genera L0/L1 para cada archivo."""
    results = []
    
    for file_path in sorted(base_path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in DOC_EXTS:
            continue
        if file_path.name.startswith("."):
            continue
        if ".tiered-context" in str(file_path):
            continue
        
        rel = str(file_path.relative_to(WORKSPACE))
        current_hash = file_hash(file_path)
        
        # En modo update, saltar si no cambió
        if update and cache.get(rel) == current_hash:
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) < 20 or len(content) > 100000:
                continue  # muy pequeño o muy grande
        except Exception:
            continue
        
        abstract = generate_abstract(file_path, content)
        overview = generate_overview(file_path, content)
        
        # Guardar L0/L1
        abstract_path = file_path.parent / f".{file_path.name}.abstract.md"
        overview_path = file_path.parent / f".{file_path.name}.overview.md"
        
        abstract_path.write_text(abstract)
        overview_path.write_text(overview)
        
        cache[rel] = current_hash
        results.append((rel, len(abstract), len(overview)))
    
    return results

def main():
    update = "--update" in sys.argv
    target_path = None
    for arg in sys.argv[1:]:
        if arg.startswith("--path="):
            target_path = WORKSPACE / arg.split("=", 1)[1]
        elif arg == "--path":
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv) and not sys.argv[idx+1].startswith("--"):
                target_path = WORKSPACE / sys.argv[idx+1]
    
    start = time.time()
    cache = load_cache()
    
    if target_path and target_path.exists():
        paths = [target_path]
    else:
        # Directorios a escanear
        paths = [
            WORKSPACE / "roadmap",
            WORKSPACE / "docs",
            WORKSPACE / "scripts",
            WORKSPACE / "proyectos",
            WORKSPACE / "memoria",
        ]
        # También archivos sueltos importantes
        for root_file in ["MANIFIESTO_LUMEN.md", "roadmap_LUMEN.md"]:
            fp = WORKSPACE / root_file
            if fp.exists():
                # Tratar como path para el scanner
                pass
    
    all_results = []
    for p in paths:
        if p.exists():
            # Si es archivo, procesar como archivo individual
            if p.is_file():
                rel = str(p.relative_to(WORKSPACE))
                current_hash = file_hash(p)
                if update and cache.get(rel) == current_hash:
                    continue
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                    if len(content) >= 20:
                        abstract = generate_abstract(p, content)
                        overview = generate_overview(p, content)
                        abstract_path = p.parent / f".{p.name}.abstract.md"
                        overview_path = p.parent / f".{p.name}.overview.md"
                        abstract_path.write_text(abstract)
                        overview_path.write_text(overview)
                        cache[rel] = current_hash
                        all_results.append((rel, len(abstract), len(overview)))
                except Exception:
                    pass
            else:
                results = process_directory(p, cache, update)
                all_results.extend(results)
    
    save_cache(cache)
    
    elapsed = time.time() - start
    mode = "update" if update else "full"
    generated = len(all_results)
    
    print(f"L0/L1 generation complete [{mode}]")
    print(f"  Files processed: {generated}")
    print(f"  Time: {elapsed:.1f}s")
    if generated > 0:
        print(f"  Avg abstract: {sum(r[1] for r in all_results)//max(generated,1)} chars")
        print(f"  Avg overview: {sum(r[2] for r in all_results)//max(generated,1)} chars")
    print(f"  Cache: {len(cache)} files tracked")
    
    # Si se generaron nuevos, indexar L0 en ChromaDB
    if generated > 0:
        print("\nIndexing L0 abstracts into ChromaDB...")
        for rel_path, ab_len, ov_len in all_results[:20]:  # limitar a 20 por tanda
            abs_path = WORKSPACE / Path(rel_path).parent / f".{Path(rel_path).name}.abstract.md"
            if abs_path.exists():
                try:
                    abstract_text = abs_path.read_text().strip()
                    sys.path.insert(0, str(SCRIPTS))
                    from memoria_vectorial import chroma_add
                    chroma_add(
                        "contextos",
                        abstract_text,
                        metadata={
                            "tipo": "l0_abstract",
                            "fuente": rel_path,
                            "largo_real": ab_len,
                        }
                    )
                except Exception as e:
                    print(f"    [{rel_path}] ChromaDB error: {e}")
        print("  Done indexing L0 abstracts.")

if __name__ == "__main__":
    main()
