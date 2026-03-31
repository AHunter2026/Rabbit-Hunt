"""
Email formatting and delivery via Gmail SMTP.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def _build_section_html(title: str, emoji: str, results: list[dict], color: str) -> str:
    """Build an HTML section for one topic."""
    if not results:
        return f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-family:Georgia,serif; color:{color}; border-bottom:2px solid {color};
                     padding-bottom:8px; margin-bottom:16px;">{emoji} {title}</h2>
          <p style="color:#888; font-style:italic;">No new results found this round.</p>
        </div>
        """

    items_html = ""
    for r in results:
        items_html += f"""
        <div style="margin-bottom:18px; padding:14px 16px; background:#f9f9f9;
                    border-left:4px solid {color}; border-radius:4px;">
          <a href="{r['url']}" style="font-size:15px; font-weight:bold; color:{color};
             text-decoration:none; font-family:Georgia,serif;">{r['title']}</a>
          <div style="font-size:12px; color:#888; margin:4px 0;">
            🔗 {r['source']}
          </div>
          <p style="font-size:13px; color:#444; margin:6px 0 0 0; line-height:1.5;">
            {r['snippet']}
          </p>
        </div>
        """

    return f"""
    <div style="margin-bottom:36px;">
      <h2 style="font-family:Georgia,serif; color:{color}; border-bottom:2px solid {color};
                 padding-bottom:8px; margin-bottom:16px;">{emoji} {title}</h2>
      {items_html}
    </div>
    """


def build_email_html(
    tamuk_results: list[dict],
    cage_design_results: list[dict],
    metal_cage_results: list[dict],
    location: str,
    radius: int,
    period: str,
) -> str:
    """Assemble full HTML email body."""

    period_emojis = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}
    period_emoji = period_emojis.get(period.lower(), "📬")
    now = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

    tamuk_section = _build_section_html(
        f"TAMUK Rabbits for Sale (within {radius} mi of {location})",
        "🐇", tamuk_results, "#5c8a3c"
    )
    cage_design_section = _build_section_html(
        "Rabbit Cage Designs",
        "🏗️", cage_design_results, "#7a5c2e"
    )
    metal_cage_section = _build_section_html(
        "Metal Rabbit Cages for Sale",
        "🛒", metal_cage_results, "#2e6b7a"
    )

    total = len(tamuk_results) + len(cage_design_results) + len(metal_cage_results)

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f0ede8; font-family:Arial,sans-serif;">
      <div style="max-width:680px; margin:0 auto; background:#fff;
                  border-radius:8px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.1);">

        <!-- Header -->
        <div style="background:#3a5c2a; padding:28px 32px;">
          <h1 style="color:#fff; font-family:Georgia,serif; margin:0; font-size:24px;">
            {period_emoji} Rabbit Scout — {period.title()} Digest
          </h1>
          <p style="color:#b8d4a0; margin:6px 0 0 0; font-size:13px;">{now}</p>
          <p style="color:#b8d4a0; margin:4px 0 0 0; font-size:13px;">
            {total} results across 3 topics
          </p>
        </div>

        <!-- Body -->
        <div style="padding:28px 32px;">
          {tamuk_section}
          {cage_design_section}
          {metal_cage_section}
        </div>

        <!-- Footer -->
        <div style="background:#f0ede8; padding:16px 32px; text-align:center;
                    font-size:12px; color:#999;">
          Rabbit Scout • Auto-generated digest • {now}
        </div>

      </div>
    </body>
    </html>
    """


def send_email(
    html_body: str,
    subject: str,
    gmail_address: str,
    gmail_app_password: str,
    recipient: str,
) -> bool:
    """Send HTML email via Gmail SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Rabbit Hunt <{gmail_address}>"
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, recipient, msg.as_string())

        print(f"[OK] Email sent to {recipient}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
