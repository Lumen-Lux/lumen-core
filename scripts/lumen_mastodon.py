#!/opt/hermes/.venv/bin/python3
"""
LUMEN Mastodon Integration Module
Script de integración con Mastodon para operaciones comunes.
Usa urllib para evitar problemas de quoting en shell.
"""
import json
import urllib.request
import urllib.parse
import sys
import os
from typing import Optional

CREDS_PATH = "/opt/data/.mastodon/credentials.json"

def _load_creds():
    with open(CREDS_PATH) as f:
        return json.load(f)

def api(method: str, path: str, data: Optional[dict] = None, raw: bool = False):
    """Llamada a la API de Mastodon. Retorna dict o None."""
    creds = _load_creds()
    base = creds["instance"] if "mastodon.social" in creds.get("instance", "") else "https://mastodon.social"
    base = f"https://{base}" if not base.startswith("http") else base
    
    url = f"{base}{path}"
    body = json.dumps(data).encode() if data else None
    
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {creds['user_token']}")
    if body:
        req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = resp.read()
            if raw:
                return result.decode()
            return json.loads(result) if result.strip() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"⚠️ HTTP {e.code}: {body[:200]}", file=sys.stderr)
        return {"error": body}

def post(status: str, visibility: str = "public", media_ids: list = None):
    """Publicar un status en Mastodon."""
    data = {"status": status, "visibility": visibility}
    if media_ids:
        data["media_ids"] = media_ids
    return api("POST", "/api/v1/statuses", data)

def timeline(timeline_type: str = "home", limit: int = 20):
    """Leer timeline. Tipos: home, local, federated, trending, list/:id"""
    return api("GET", f"/api/v1/timelines/{timeline_type}?limit={limit}")

def notifications(limit: int = 20):
    """Obtener notificaciones."""
    return api("GET", f"/api/v1/notifications?limit={limit}")

def search(query: str, limit: int = 10):
    """Buscar en Mastodon (cuentas, hashtags, statuses)."""
    return api("GET", f"/api/v2/search?q={urllib.parse.quote(query)}&limit={limit}")

def account_info(account_id: str = None):
    """Obtener info de cuenta. Por defecto la propia."""
    if account_id:
        return api("GET", f"/api/v1/accounts/{account_id}")
    return api("GET", "/api/v1/accounts/verify_credentials")

def follow(account_id: str):
    """Seguir una cuenta."""
    return api("POST", f"/api/v1/accounts/{account_id}/follow")

def fav(status_id: str):
    """Dar fav a un status."""
    return api("POST", f"/api/v1/statuses/{status_id}/favourite")

def boost(status_id: str):
    """Boostear un status."""
    return api("POST", f"/api/v1/statuses/{status_id}/reblog")

def reply(status_id: str, text: str, visibility: str = "public"):
    """Responder a un status."""
    return api("POST", "/api/v1/statuses", {
        "status": text,
        "in_reply_to_id": status_id,
        "visibility": visibility
    })

def home_dashboard():
    """Obtener home + resumen de actividad (similar a Moltbook /home)."""
    tl = timeline("home", 20)
    notif = notifications(5)
    me = account_info()
    return {
        "account": me,
        "timeline": tl,
        "notifications": notif
    }

def update_profile(display_name: str = None, note: str = None, bot: bool = None):
    """Actualizar perfil."""
    data = {}
    if display_name: data["display_name"] = display_name
    if note: data["note"] = note
    if bot is not None: data["bot"] = 1 if bot else 0
    return api("PATCH", "/api/v1/accounts/update_credentials", data)

# --- CLI entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: lumen_mastodon.py <comando> [args]")
        print("Comandos: post, timeline, notifications, search, info, dashboard, profile")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "post":
        text = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip()
        vis = sys.argv[3] if len(sys.argv) > 3 else "public"
        r = post(text, vis)
        if r and "url" in r:
            print(f"✅ Publicado: {r['url']}")
        else:
            print(f"❌ Error: {r}")
    
    elif cmd == "timeline":
        tl_type = sys.argv[2] if len(sys.argv) > 2 else "home"
        r = timeline(tl_type)
        if isinstance(r, list):
            for s in r[:10]:
                user = s.get("account", {}).get("acct", "?")
                content = s.get("content", "")[:100]
                print(f"  @{user}: {content}")
        else:
            print(json.dumps(r, indent=2)[:500])
    
    elif cmd == "dashboard":
        r = home_dashboard()
        acct = r["account"]
        print(f"📊 @{acct.get('acct','?')} | Followers: {acct.get('followers_count',0)} | Following: {acct.get('following_count',0)} | Posts: {acct.get('statuses_count',0)}")
        notif_count = len(r["notifications"]) if isinstance(r["notifications"], list) else 0
        tl_count = len(r["timeline"]) if isinstance(r["timeline"], list) else 0
        print(f"📬 Notificaciones: {notif_count}")
        print(f"📰 Timeline: {tl_count} posts")
    
    elif cmd == "info":
        r = account_info(sys.argv[2] if len(sys.argv) > 2 else None)
        print(json.dumps(r, indent=2)[:1000])
    
    else:
        print(f"Comando desconocido: {cmd}")
