#!/opt/hermes/.venv/bin/python3
"""
lumen_mail.py — Cliente de correo para LUMEN.
SMTP (enviar) + IMAP (recibir) sobre Gmail.

Uso:
  lumen_mail.py send --to destinatario@email.com --asunto "Texto" --cuerpo "Mensaje"
  lumen_mail.py inbox [--limite 5]
  lumen_mail.py read --id <msg_id>
  lumen_mail.py search --query "palabras clave"
  lumen_mail.py test-conexion

Requiere variables de entorno o archivo ~/.lumen/mail_creds.json:
  LUMEN_MAIL_USER=proyecto.lumen.lux@gmail.com
  LUMEN_MAIL_PASS=contraseña
"""

import os
import sys
import json
import argparse
import email
import imaplib
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────

CREDS_FILE = Path.home() / ".lumen" / "mail_creds.json"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


def _get_creds():
    """Obtiene credenciales: primero env vars, luego archivo."""
    user = os.environ.get("LUMEN_MAIL_USER")
    password = os.environ.get("LUMEN_MAIL_PASS")

    if user and password:
        return user, password

    if CREDS_FILE.exists():
        try:
            data = json.loads(CREDS_FILE.read_text())
            return data.get("user"), data.get("password")
        except (json.JSONDecodeError, KeyError):
            pass

    return None, None


def _save_creds(user, password):
    """Guarda credenciales de forma persistente."""
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDS_FILE.write_text(json.dumps({"user": user, "password": password}, indent=2))
    os.chmod(CREDS_FILE, 0o600)  # Solo el usuario puede leer
    print(f"🔐 Credenciales guardadas en {CREDS_FILE}")


def _decode_header_value(value):
    """Decodifica cabeceras de email codificadas."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def cmd_test():
    """Prueba conexión SMTP e IMAP."""
    user, password = _get_creds()
    if not user or not password:
        print("❌ No hay credenciales configuradas.")
        print("   Usa: lumen_mail.py config --user user@gmail.com")
        print("   O define LUMEN_MAIL_USER y LUMEN_MAIL_PASS en entorno.")
        return False

    ok = True

    # SMTP
    try:
        print(f"🔌 Probando SMTP ({SMTP_SERVER}:{SMTP_PORT})...")
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, password)
        print(f"   ✅ SMTP: conexión exitosa")
        smtp.quit()
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ SMTP: autenticación fallida — {e}")
        print("   → Gmail rechaza contraseña directa. Necesitas:")
        print("     1. Activar verificación en dos pasos en tu cuenta Google")
        print("     2. Generar una 'App Password' en https://myaccount.google.com/apppasswords")
        print("     3. Configurarla con: lumen_mail.py config --pass <app_password>")
        ok = False
    except Exception as e:
        print(f"   ❌ SMTP: error — {e}")
        ok = False

    # IMAP
    try:
        print(f"🔌 Probando IMAP ({IMAP_SERVER}:{IMAP_PORT})...")
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(user, password)
        print(f"   ✅ IMAP: conexión exitosa")
        imap.logout()
    except imaplib.IMAP4.error as e:
        print(f"   ❌ IMAP: autenticación fallida — {e}")
        ok = False
    except Exception as e:
        print(f"   ❌ IMAP: error — {e}")
        ok = False

    if ok:
        print(f"\n✅ LUMEN puede enviar y recibir correos desde {user}")
    else:
        print(f"\n⚠️  Configuración incompleta. Revisa los errores arriba.")

    return ok


def cmd_config(user=None, password=None):
    """Configura credenciales."""
    if not user:
        user = input("  Email: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("  Contraseña: ")

    _save_creds(user, password)
    print(f"✅ Credenciales guardadas para {user}")
    print("   Verifica la conexión con: lumen_mail.py test-conexion")


def cmd_send(to, subject, body, cc=None, bcc=None):
    """Envía un email."""
    user, password = _get_creds()
    if not user or not password:
        print("❌ Credenciales no configuradas. Usa 'lumen_mail.py config' primero.")
        return False

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if cc:
        msg["Cc"] = cc

    recipients = [to]
    if cc:
        recipients += [c.strip() for c in cc.split(",")]
    if bcc:
        recipients += [c.strip() for c in bcc.split(",")]

    try:
        print(f"📤 Enviando a {to}...")
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, password)
        smtp.sendmail(user, recipients, msg.as_string())
        smtp.quit()
        print(f"✅ Enviado: '{subject}' → {to}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Autenticación SMTP fallida.")
        print("   → Necesitas una App Password de Google.")
        print("     https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"❌ Error al enviar: {e}")
        return False


def cmd_inbox(limit=5, folder="INBOX"):
    """Lista emails de la bandeja de entrada."""
    user, password = _get_creds()
    if not user or not password:
        print("❌ Credenciales no configuradas.")
        return

    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(user, password)
        imap.select(folder)

        status, messages = imap.search(None, "ALL")
        if status != "OK":
            print("📭 No se pudieron listar mensajes")
            imap.logout()
            return

        msg_ids = messages[0].split()
        if not msg_ids:
            print("📭 Bandeja vacía")
            imap.logout()
            return

        # Últimos N mensajes
        recent = msg_ids[-limit:]

        print(f"\n📬 {folder} — últimos {len(recent)} de {len(msg_ids)} mensajes:")
        print()

        for mid in reversed(recent):
            status, data = imap.fetch(mid, "(RFC822)")
            if status != "OK":
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_ = _decode_header_value(msg.get("From"))
            subj = _decode_header_value(msg.get("Subject")) or "(sin asunto)"
            date = msg.get("Date", "?")
            flags = msg.get("X-Gmail-Labels", "")

            # Truncar asunto largo
            subj_short = subj if len(subj) < 60 else subj[:57] + "..."

            print(f"  [{mid}] {date[:25]}")
            print(f"        De: {from_}")
            print(f"        Asunto: {subj_short}")
            print()

        imap.logout()

    except imaplib.IMAP4.error as e:
        print(f"❌ Error IMAP: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_read(msg_id, folder="INBOX"):
    """Lee un email completo por ID."""
    user, password = _get_creds()
    if not user or not password:
        print("❌ Credenciales no configuradas.")
        return

    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(user, password)
        imap.select(folder)

        status, data = imap.fetch(str(msg_id), "(RFC822)")
        if status != "OK":
            print(f"❌ No se pudo leer el mensaje {msg_id}")
            imap.logout()
            return

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        print(f"\n📄 Mensaje #{msg_id}")
        print(f"   {'='*50}")
        print(f"   De:     {_decode_header_value(msg.get('From'))}")
        print(f"   Para:   {_decode_header_value(msg.get('To'))}")
        print(f"   Fecha:  {msg.get('Date', '?')}")
        print(f"   Asunto: {_decode_header_value(msg.get('Subject'))}")
        print(f"   {'='*50}")
        print()

        # Extraer cuerpo
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                    except (LookupError, UnicodeDecodeError):
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            try:
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        print(body.strip() if body else "(sin contenido textual)")

        imap.logout()

    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_search(query, folder="INBOX", limit=10):
    """Busca emails por texto en cabeceras."""
    user, password = _get_creds()
    if not user or not password:
        print("❌ Credenciales no configuradas.")
        return

    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(user, password)
        imap.select(folder)

        # Búsqueda IMAP
        status, messages = imap.search(None, f'SUBJECT "{query}"', f'FROM "{query}"', f'TEXT "{query}"')
        if status != "OK":
            print(f"No se encontraron resultados para: {query}")
            imap.logout()
            return

        # IMAP search con múltiples criterios usa OR
        # Simple: buscar en asunto
        status, messages = imap.search(None, f'(OR SUBJECT "{query}" FROM "{query}")')
        if status != "OK" or not messages[0]:
            # Fallback: buscar en todo el texto
            status, messages = imap.search(None, f'TEXT "{query}"')

        if status != "OK" or not messages[0]:
            print(f"📭 Sin resultados para: {query}")
            imap.logout()
            return

        msg_ids = messages[0].split()
        print(f"\n🔍 {len(msg_ids)} resultado(s) para: '{query}'")
        print()

        for mid in msg_ids[:limit]:
            status, data = imap.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_ = _decode_header_value(msg.get("From"))
            subj = _decode_header_value(msg.get("Subject")) or "(sin asunto)"
            date = msg.get("Date", "?")[:25]

            print(f"  [{mid.decode() if isinstance(mid, bytes) else mid}] {date}")
            print(f"        De: {from_} — {subj[:70]}")
            print()

        imap.logout()

    except Exception as e:
        print(f"❌ Error: {e}")


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📧 LUMEN Mail — Cliente de correo para LUMEN"
    )
    sub = parser.add_subparsers(dest="command")

    # config
    p_cfg = sub.add_parser("config", help="Configurar credenciales")
    p_cfg.add_argument("--user", help="Dirección de email")
    p_cfg.add_argument("--pass", dest="password", help="Contraseña o App Password")

    # test
    sub.add_parser("test-conexion", help="Probar conexión SMTP+IMAP")

    # send
    p_send = sub.add_parser("send", help="Enviar email")
    p_send.add_argument("--to", required=True, help="Destinatario")
    p_send.add_argument("--asunto", required=True, help="Asunto")
    p_send.add_argument("--cuerpo", required=True, help="Cuerpo del mensaje")
    p_send.add_argument("--cc", help="CC")
    p_send.add_argument("--bcc", help="BCC")

    # inbox
    p_inbox = sub.add_parser("inbox", help="Ver bandeja de entrada")
    p_inbox.add_argument("--limite", type=int, default=5, help="Máximo de mensajes")
    p_inbox.add_argument("--carpeta", default="INBOX", help="Carpeta IMAP")

    # read
    p_read = sub.add_parser("read", help="Leer un email")
    p_read.add_argument("--id", required=True, help="ID del mensaje")
    p_read.add_argument("--carpeta", default="INBOX")

    # search
    p_search = sub.add_parser("search", help="Buscar emails")
    p_search.add_argument("--query", required=True, help="Texto a buscar")
    p_search.add_argument("--limite", type=int, default=10)
    p_search.add_argument("--carpeta", default="INBOX")

    args = parser.parse_args()

    if args.command == "config":
        cmd_config(args.user, args.password)
    elif args.command == "test-conexion":
        cmd_test()
    elif args.command == "send":
        cmd_send(args.to, args.asunto, args.cuerpo, cc=args.cc, bcc=args.bcc)
    elif args.command == "inbox":
        cmd_inbox(limit=args.limite, folder=args.carpeta)
    elif args.command == "read":
        cmd_read(args.id, folder=args.carpeta)
    elif args.command == "search":
        cmd_search(args.query, limit=args.limite, folder=args.carpeta)
    else:
        parser.print_help()
        print("\n   Comandos: config, test-conexion, send, inbox, read, search")


if __name__ == "__main__":
    main()
