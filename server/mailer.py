import logging
from typing import Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

def render_license_email_html(customer_email: str, license_key: str, billing_mode: str) -> str:
    """
    Renders clean, developer-focused HTML email for license activation.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Your Schemap Pro License</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 32px; }}
    .logo {{ color: #38bdf8; font-weight: 700; font-size: 20px; letter-spacing: -0.5px; text-decoration: none; }}
    h1 {{ font-size: 22px; color: #f8fafc; margin-top: 16px; margin-bottom: 8px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; }}
    .key-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 16px; font-family: "JetBrains Mono", monospace; font-size: 14px; color: #38bdf8; word-break: break-all; margin-bottom: 24px; text-align: center; }}
    .cmd-box {{ background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 18px; font-family: monospace; font-size: 13px; color: #4ade80; margin-bottom: 24px; }}
    .btn {{ display: inline-block; background: #0284c7; color: #ffffff; text-decoration: none; font-weight: 600; padding: 12px 24px; border-radius: 6px; font-size: 14px; }}
    .footer {{ margin-top: 32px; font-size: 12px; color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <a class="logo" href="https://schemap.com">SCHEMAP</a>
    <h1>Welcome to Schemap Pro</h1>
    <p>Thank you for purchasing <strong>Schemap Pro ({billing_mode.capitalize()})</strong>! Here is your official license key:</p>
    
    <div class="key-box">{license_key}</div>
    
    <p>To activate Schemap Pro on your machine, open your terminal and run:</p>
    
    <div class="cmd-box">$ schemap activate {license_key}</div>
    
    <p>Your license credentials will be saved locally in your OS app directory and applied to all your database context compilations and CI pipelines.</p>
    
    <div class="footer">
      <p>© 2026 Schemap · Local-First Database Context Compiler</p>
    </div>
  </div>
</body>
</html>
"""

def send_license_email(recipient_email: str, license_key: str, billing_mode: str) -> Dict[str, Any]:
    """
    Sends license delivery email using Resend API if API key is set, otherwise logs output.
    """
    subject = "Your Schemap Pro License Key"
    html_content = render_license_email_html(recipient_email, license_key, billing_mode)

    if settings.RESEND_API_KEY:
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            params = {
                "from": settings.FROM_EMAIL,
                "to": [recipient_email],
                "subject": subject,
                "html": html_content,
            }
            email_res = resend.Emails.send(params)
            logger.info(f"Email dispatched via Resend to {recipient_email}: {email_res}")
            return {"status": "sent", "resend_id": getattr(email_res, "id", str(email_res))}
        except Exception as e:
            logger.error(f"Failed to send email via Resend to {recipient_email}: {str(e)}")
            raise RuntimeError(f"Resend email dispatch error: {str(e)}")
    else:
        logger.info(f"[MOCK MAIL] To: {recipient_email} | Subject: {subject} | Key: {license_key[:16]}...")
        return {"status": "mock_sent", "recipient": recipient_email}
