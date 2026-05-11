"""
IMAP IDLE email listener — AC-002.

Uses imaplib with IDLE command for near-real-time notification.
Falls back to 5-minute polling if IDLE is not supported.

The listener is a blocking loop — run in a dedicated thread per active role.
"""

import email
import imaplib
import os
import re
import select
import socket
import time
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class RawEmail:
    uid: str
    subject: str
    sender_email: str
    sender_name: str
    body_text: str
    attachments: list[dict] = field(default_factory=list)
    # Each attachment: {filename, data: bytes, content_type}


_SUBJECT_PATTERN = re.compile(r"APPLY[-_]([A-Z0-9]+)", re.IGNORECASE)
_IDLE_TIMEOUT = 25 * 60   # 25 min (RFC 2177 recommends < 29 min)
_POLL_INTERVAL = 5 * 60   # 5-min fallback


def _imap_connect() -> imaplib.IMAP4_SSL:
    host = os.environ["IMAP_HOST"]
    port = int(os.environ.get("IMAP_PORT", "993"))
    user = os.environ["IMAP_USER"]
    password = os.environ["IMAP_PASSWORD"]

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, password)
    conn.select("INBOX")
    return conn


def _supports_idle(conn: imaplib.IMAP4_SSL) -> bool:
    try:
        caps = conn.capabilities
        return b"IDLE" in caps
    except Exception:
        return False


def _fetch_unseen(conn: imaplib.IMAP4_SSL, role_id: str) -> list[str]:
    """Return UIDs of unseen emails whose subject matches APPLY-{role_id}."""
    # Search for unseen emails with matching subject
    search_criteria = f'(UNSEEN SUBJECT "APPLY-{role_id}")'
    status, data = conn.uid("search", None, search_criteria)
    if status != "OK" or not data[0]:
        return []
    return data[0].split()


def _parse_email(raw_data: bytes) -> RawEmail | None:
    msg = email.message_from_bytes(raw_data)

    # Decode subject
    subject_raw = msg.get("Subject", "")
    subject = email.header.decode_header(subject_raw)
    subject_parts = []
    for part, charset in subject:
        if isinstance(part, bytes):
            subject_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            subject_parts.append(part)
    subject = " ".join(subject_parts)

    # Sender
    from_raw = msg.get("From", "")
    sender_name, sender_email_addr = email.utils.parseaddr(from_raw)

    body_text = ""
    attachments = []

    for part in msg.walk():
        ctype = part.get_content_type()
        disposition = str(part.get("Content-Disposition", ""))

        if ctype == "text/plain" and "attachment" not in disposition:
            payload = part.get_payload(decode=True)
            if payload:
                body_text += payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        elif "attachment" in disposition or ctype in (
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            filename = part.get_filename() or "attachment"
            data = part.get_payload(decode=True)
            if data:
                attachments.append({
                    "filename": filename,
                    "data": data,
                    "content_type": ctype,
                })

    return RawEmail(
        uid="",
        subject=subject,
        sender_email=sender_email_addr,
        sender_name=sender_name,
        body_text=body_text,
        attachments=attachments,
    )


def listen(role_id: str, stop_event, on_email_received) -> None:
    """Block until stop_event is set, calling on_email_received for each valid email.

    Args:
        role_id: The role identifier (first 8 chars of job UUID).
        stop_event: threading.Event — set to stop the listener.
        on_email_received: callable(RawEmail) called for each matched email.
    """
    conn = _imap_connect()
    use_idle = _supports_idle(conn)

    while not stop_event.is_set():
        try:
            uids = _fetch_unseen(conn, role_id)
            for uid in uids:
                status, msg_data = conn.uid("fetch", uid, "(RFC822)")
                if status != "OK":
                    continue
                raw = _parse_email(msg_data[0][1])
                if raw:
                    raw.uid = uid.decode() if isinstance(uid, bytes) else uid
                    on_email_received(raw)
                # Mark as seen
                conn.uid("store", uid, "+FLAGS", "\\Seen")

            if use_idle:
                _idle_wait(conn, _IDLE_TIMEOUT)
            else:
                time.sleep(_POLL_INTERVAL)

        except imaplib.IMAP4.abort:
            # Connection dropped — reconnect
            try:
                conn.logout()
            except Exception:
                pass
            conn = _imap_connect()
            use_idle = _supports_idle(conn)

        except Exception:
            time.sleep(30)   # brief back-off on unexpected error


def _idle_wait(conn: imaplib.IMAP4_SSL, timeout: int) -> None:
    """Send IDLE command and wait for server notification or timeout."""
    conn.send(b"A001 IDLE\r\n")
    conn.readline()  # "+" continuation response

    deadline = time.time() + timeout
    sock = conn.socket()
    sock.settimeout(1)

    while time.time() < deadline:
        try:
            data = sock.recv(4096)
            if data and b"EXISTS" in data:
                break
        except socket.timeout:
            pass
        except Exception:
            break

    # Send DONE to exit IDLE
    try:
        conn.send(b"DONE\r\n")
        conn.readline()
    except Exception:
        pass
