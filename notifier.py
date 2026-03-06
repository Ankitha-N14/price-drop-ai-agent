"""
notifier.py -- Email (SMTP/Gmail) price-alert notifier
Reads credentials from environment variables OR config.json.

Gmail setup:
  1. Enable 2-Step Verification on your Google account
  2. Google Account -> Security -> App Passwords -> generate one
  3. Paste that password as EMAIL_PASSWORD (NOT your regular password)

Environment variables (or set same keys in config.json):
  EMAIL_SENDER    your Gmail address
  EMAIL_PASSWORD  Gmail App Password
  EMAIL_RECEIVER  where to send (defaults to EMAIL_SENDER)
  SMTP_HOST       default: smtp.gmail.com
  SMTP_PORT       default: 587
"""

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

log = logging.getLogger(__name__)
CONFIG_FILE = Path("config.json")


def _get(key, fallback=""):
    val = os.environ.get(key, "").strip()
    if val: return val
    if CONFIG_FILE.exists():
        try:
            return str(json.loads(CONFIG_FILE.read_text()).get(key, fallback)).strip()
        except Exception:
            pass
    return fallback


class EmailNotifier:
    def __init__(self):
        self.sender   = _get("EMAIL_SENDER")
        self.password = _get("EMAIL_PASSWORD")
        self.receiver = _get("EMAIL_RECEIVER") or self.sender
        self.host     = _get("SMTP_HOST", "smtp.gmail.com")
        self.port     = int(_get("SMTP_PORT", "587"))

        if not self.sender or not self.password:
            log.warning(
                "Email not configured. Set EMAIL_SENDER and EMAIL_PASSWORD "
                "in environment variables or config.json."
            )
        else:
            log.info("Email ready: %s -> %s", self.sender, self.receiver)

    @property
    def enabled(self):
        return bool(self.sender and self.password)

    def send(self, body, subject="Price Alert!"):
        if not self.enabled:
            log.warning("Email skipped (not configured). Alert (console):\n%s", body)
            print("\n" + "="*60)
            print("PRICE ALERT (email not configured):")
            print(body)
            print("="*60 + "\n")
            return False

        msg            = MIMEMultipart("alternative")
        msg["From"]    = self.sender
        msg["To"]      = self.receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        html = body.replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
        html_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body  {{ font-family:Arial,sans-serif; background:#f4f4f4; padding:20px; }}
  .card {{ background:#fff; border-radius:10px; padding:28px 32px;
           max-width:520px; margin:auto; box-shadow:0 4px 16px rgba(0,0,0,.12); }}
  h2    {{ color:#e44d26; margin:0 0 16px; }}
  p     {{ line-height:1.7; color:#333; }}
  a     {{ color:#0070f3; }}
  .tip  {{ background:#e8f5e9; border-left:4px solid #43a047;
           padding:10px 14px; border-radius:4px; margin-top:12px; }}
</style></head>
<body><div class="card">
  <h2>Price Drop Detected!</h2>
  <p>{html}</p>
  <div class="tip">Check the product page to confirm stock before purchasing.</div>
</div></body></html>"""
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.ehlo(); server.starttls(); server.ehlo()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.receiver, msg.as_string())
            log.info("Email sent to %s | %s", self.receiver, subject)
            return True

        except smtplib.SMTPAuthenticationError:
            log.error(
                "Email auth failed. Use a Gmail APP PASSWORD, not your account password.\n"
                "Guide: https://support.google.com/accounts/answer/185833"
            )
        except smtplib.SMTPRecipientsRefused:
            log.error("Recipient refused: %s", self.receiver)
        except smtplib.SMTPException as e:
            log.error("SMTP error: %s", e)
        except TimeoutError:
            log.error("SMTP timed out. Check SMTP_HOST/SMTP_PORT.")
        except OSError as e:
            log.error("Network error: %s", e)
        return False

    def test(self):
        return self.send(
            body=(
                "Test notification from your Price Monitor\n\n"
                f"Sender  : {self.sender}\n"
                f"Receiver: {self.receiver}\n"
                f"Host    : {self.host}:{self.port}\n\n"
                "If you received this, email alerts are working!"
            ),
            subject="Price Monitor -- Test Email",
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = EmailNotifier().test()
    print("Test:", "SUCCESS" if ok else "FAILED -- check logs above")
