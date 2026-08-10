export interface MailOptions {
  apiKey: string;
  fromEmail: string;
  toEmail: string;
  licenseKey: string;
  billingMode: string;
}

export function renderLicenseEmailHtml(licenseKey: string, billingMode: string): string {
  const modeCap = billingMode.charAt(0).toUpperCase() + billingMode.slice(1);
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Your Schemap Pro License</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; margin: 0; padding: 40px 20px; }
    .container { max-width: 600px; margin: 0 auto; background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 32px; }
    .logo { color: #38bdf8; font-weight: 700; font-size: 20px; letter-spacing: -0.5px; text-decoration: none; }
    h1 { font-size: 22px; color: #f8fafc; margin-top: 16px; margin-bottom: 8px; }
    p { font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; }
    .key-box { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 16px; font-family: monospace; font-size: 14px; color: #38bdf8; word-break: break-all; margin-bottom: 24px; text-align: center; }
    .cmd-box { background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 18px; font-family: monospace; font-size: 13px; color: #4ade80; margin-bottom: 24px; }
    .footer { margin-top: 32px; font-size: 12px; color: #64748b; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <a class="logo" href="https://schemap-tool.pages.dev">SCHEMAP</a>
    <h1>Welcome to Schemap Pro</h1>
    <p>Thank you for purchasing <strong>Schemap Pro (${modeCap})</strong>! Here is your official license key:</p>
    
    <div class="key-box">${licenseKey}</div>
    
    <p>To activate Schemap Pro on your machine, open your terminal and run:</p>
    
    <div class="cmd-box">$ schemap activate ${licenseKey}</div>
    
    <p>Your license credentials will be saved locally in your OS app directory and applied to all your database context compilations and CI pipelines.</p>
    
    <div class="footer">
      <p>© 2026 Schemap · Local-First Database Context Compiler</p>
    </div>
  </div>
</body>
</html>`;
}

export async function sendLicenseEmail(opts: MailOptions): Promise<void> {
  if (!opts.apiKey) {
    console.log(`[MOCK MAIL] To: ${opts.toEmail} | Key: ${opts.licenseKey.slice(0, 16)}...`);
    return;
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${opts.apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: opts.fromEmail,
      to: [opts.toEmail],
      subject: "Your Schemap Pro License Key",
      html: renderLicenseEmailHtml(opts.licenseKey, opts.billingMode)
    })
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Resend email dispatch error (${res.status}): ${errorText}`);
  }
}
