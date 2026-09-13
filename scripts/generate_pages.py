#!/usr/bin/env python3
"""Schemap Programmatic SEO Page Generator"""
import os
from datetime import date

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
SITEMAP_PATH = os.path.join(DOCS_DIR, "sitemap.xml")
TODAY = date.today().strftime("%Y-%m-%d")
YEAR = date.today().year

DATABASES = [
    {"slug": "postgresql", "name": "PostgreSQL", "short": "Postgres", "install_hint": "postgresql://user:pass@localhost/dbname", "description": "the world's most advanced open-source relational database"},
    {"slug": "supabase", "name": "Supabase", "short": "Supabase", "install_hint": "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres", "description": "the open-source Firebase alternative powered by PostgreSQL"},
    {"slug": "neon", "name": "Neon", "short": "Neon Postgres", "install_hint": "postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require", "description": "the serverless multi-tenant PostgreSQL cloud architecture"},
    {"slug": "sqlite", "name": "SQLite", "short": "SQLite", "install_hint": "sqlite:///path/to/database.db", "description": "the most widely deployed SQL database engine"},
    {"slug": "mysql", "name": "MySQL", "short": "MySQL", "install_hint": "mysql://user:pass@localhost/dbname", "description": "the world's most popular open-source relational database"},
    {"slug": "turso", "name": "Turso", "short": "Turso", "install_hint": "libsql://your-db.turso.io", "description": "the edge-native libSQL database built on SQLite"},
    {"slug": "oracle", "name": "Oracle", "short": "Oracle", "install_hint": "oracle+cx_oracle://user:pass@host/service", "description": "Oracle Database, the enterprise-grade relational database"},
]

AGENTS = [
    {"slug": "cursor", "name": "Cursor", "file": ".cursor/rules/schemap.mdc", "file_short": ".mdc rules", "cmd_flag": "--targets cursor", "description": "the AI-first code editor", "context_noun": "Cursor rules"},
    {"slug": "claude-code", "name": "Claude Code", "file": "CLAUDE.md", "file_short": "CLAUDE.md", "cmd_flag": "--targets claude", "description": "Anthropic's agentic AI coding CLI", "context_noun": "CLAUDE.md database context"},
    {"slug": "windsurf", "name": "Windsurf", "file": ".windsurfrules", "file_short": ".windsurfrules", "cmd_flag": "--targets cursor", "description": "Codeium's agentic AI IDE", "context_noun": "Windsurf database context rules"},
    {"slug": "codex", "name": "OpenAI Codex / Codex CLI", "file": "AGENTS.md", "file_short": "AGENTS.md", "cmd_flag": "--targets codex", "description": "OpenAI's coding agent and Codex CLI", "context_noun": "AGENTS.md database context"},
    {"slug": "copilot", "name": "GitHub Copilot", "file": ".github/copilot-instructions.md", "file_short": "copilot-instructions.md", "cmd_flag": "--targets copilot", "description": "GitHub's AI pair programmer", "context_noun": "Copilot database instructions"},
]

SITEMAP_ENTRY = """  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.75</priority>
  </url>"""

def build_page(db, agent):
    slug = f"for-{db['slug']}-{agent['slug']}"
    url = f"https://schemap-tool.pages.dev/{slug}.html"
    title = f"{db['name']} Database Context for {agent['name']} | Schemap"
    desc = (f"Give {agent['name']} accurate {db['name']} schema context in seconds. "
            f"Schemap compiles your {db['short']} schema into {agent['file_short']} "
            f"preventing hallucinated JOINs and cutting token costs by 89%%.")
    headline = f"How to Give {agent['name']} {db['name']} Database Context"
    faq1_q = f"How do I give {agent['name']} {db['name']} database context?"
    faq1_a = (f"Install Schemap with pipx install schemap-tool, connect to your {db['short']} database "
              f"({db['install_hint']}), then run schemap agents {agent['cmd_flag']} to auto-generate "
              f"{agent['file']} with full schema context, foreign key maps, and anti-hallucination safety rules.")
    faq2_q = f"Does Schemap support {db['name']} with {agent['name']}?"
    faq2_a = (f"Yes. Schemap fully supports {db['name']} ({db['description']}) and generates native "
              f"{agent['context_noun']} that {agent['name']} reads automatically from your project directory.")
    faq3_q = f"What makes Schemap better than manually writing {agent['file_short']} for {db['short']}?"
    faq3_a = (f"Manual schema files go stale instantly. Schemap runs in sub-3ms, auto-infers foreign keys, "
              f"injects SAFETY guardrails, and compresses your {db['short']} schema by up to 89%% "
              f"so {agent['name']} always has accurate context.")

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="https://schemap-tool.pages.dev/assets/Icon%20Dark.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="https://schemap-tool.pages.dev/assets/Icon%20Dark.png">
    <link rel="icon" href="assets/Icon Dark.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,700;1,400&family=Red+Hat+Display:wght@400;500;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css?v=13">
    <script async src="https://startupbar.co/widget/loader.js" data-startup-id="6a520807-b62b-4145-8c05-b2c862af8e05"></script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "TechArticle",
      "headline": "{headline}",
      "description": "{desc}",
      "url": "{url}",
      "inLanguage": "en",
      "articleSection": "Developer Integration Guide",
      "datePublished": "{TODAY}",
      "dateModified": "{TODAY}",
      "author": {{"@type": "Person", "name": "Alan Syahmi", "url": "https://github.com/alansyahmi"}},
      "publisher": {{"@type": "Organization", "name": "Schemap", "url": "https://schemap-tool.pages.dev/"}}
    }}
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{"@type": "Question", "name": "{faq1_q}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq1_a}"}}}},
        {{"@type": "Question", "name": "{faq2_q}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq2_a}"}}}},
        {{"@type": "Question", "name": "{faq3_q}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq3_a}"}}}}
      ]
    }}
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Schemap", "item": "https://schemap-tool.pages.dev/"}},
        {{"@type": "ListItem", "position": 2, "name": "Guides", "item": "https://schemap-tool.pages.dev/blog.html"}},
        {{"@type": "ListItem", "position": 3, "name": "{db['name']} + {agent['name']}", "item": "{url}"}}
      ]
    }}
    </script>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a class="logo" href="index.html" aria-label="Schemap home">
                <img src="assets/Text_Logo__Dark_-removebg-preview2.png" alt="Schemap">
            </a>
            <div class="nav-links">
                <a href="index.html#how-it-works">How it works</a>
                <a href="index.html#features">Features</a>
                <a href="blog.html">Blog</a>
                <a href="docs.html">Docs</a>
                <a href="index.html#pricing">Pricing</a>
                <a href="https://billing.stripe.com/p/login/28EaEXgO9dZ36S44fddIA00" target="_blank" rel="noopener">Manage Subscription</a>
                <a class="nav-btn" href="https://github.com/alansyahmi/Schemap" target="_blank" rel="noopener">GitHub</a>
            </div>
        </div>
    </nav>
    <main>
        <section style="max-width:820px;margin:80px auto 0;padding:0 24px;">
            <nav aria-label="Breadcrumb" style="margin-bottom:24px;font-size:.85rem;color:var(--muted);">
                <a href="index.html" style="color:var(--muted);text-decoration:none;">Schemap</a>
                <span style="margin:0 8px;">&rsaquo;</span>
                <a href="blog.html" style="color:var(--muted);text-decoration:none;">Guides</a>
                <span style="margin:0 8px;">&rsaquo;</span>
                <span style="color:var(--text);">{db['name']} + {agent['name']}</span>
            </nav>
            <span style="background:var(--surface2);color:var(--muted);padding:4px 10px;border-radius:4px;font-size:.8rem;font-weight:600;letter-spacing:.04em;">Integration Guide</span>
            <h1 style="margin-top:16px;font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.2;">{headline}</h1>
            <p style="margin-top:16px;font-size:1.1rem;color:var(--muted);line-height:1.7;">{desc}</p>
            <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
                <a class="btn btn-primary" href="index.html#installation">Install Schemap Free</a>
                <a class="btn btn-secondary" href="https://github.com/alansyahmi/Schemap" target="_blank" rel="noopener">View on GitHub</a>
            </div>
        </section>
        <article style="max-width:820px;margin:60px auto 80px;padding:0 24px;">
            <h2>Why {agent['name']} Needs Explicit {db['name']} Schema Context</h2>
            <p>{agent['name']} is {agent['description']}. Like all LLM-powered coding tools, it has no native awareness of your database. Without explicit schema context, it will hallucinate JOIN paths, reference non-existent columns, query sensitive fields, and waste thousands of tokens per prompt.</p>
            <p>Schemap solves this by extracting your live {db['name']} schema and compiling it into <code>{agent['file']}</code> &mdash; a file {agent['name']} reads automatically from your project root.</p>

            <h2>Quickstart: {db['name']} + {agent['name']} in 3 Steps</h2>
            <h3>Step 1 &mdash; Install Schemap</h3>
            <div class="terminal" style="margin:16px 0;">
                <div class="terminal-bar"><span style="color:var(--subtle);font-size:.75rem;">bash</span></div>
                <div class="terminal-body" style="padding:16px 20px;"><pre style="margin:0;font-size:.9rem;"><code>pipx install schemap-tool
# or: uv tool install schemap-tool</code></pre></div>
            </div>
            <h3>Step 2 &mdash; Connect to {db['name']}</h3>
            <div class="terminal" style="margin:16px 0;">
                <div class="terminal-bar"><span style="color:var(--subtle);font-size:.75rem;">bash</span></div>
                <div class="terminal-body" style="padding:16px 20px;"><pre style="margin:0;font-size:.9rem;"><code>schemap quickstart
# Enter: {db['install_hint']}</code></pre></div>
            </div>
            <h3>Step 3 &mdash; Generate {agent['context_noun']}</h3>
            <div class="terminal" style="margin:16px 0;">
                <div class="terminal-bar"><span style="color:var(--subtle);font-size:.75rem;">bash</span></div>
                <div class="terminal-body" style="padding:16px 20px;"><pre style="margin:0;font-size:.9rem;"><code>schemap agents {agent['cmd_flag']}
# Wrote {agent['file']} with safety guardrails in 2ms</code></pre></div>
            </div>

            <h2>What Schemap Injects into {agent['file_short']}</h2>
            <ul>
                <li><strong>Table Map</strong> &mdash; every {db['short']} table with column types</li>
                <li><strong>Foreign Key Graph</strong> &mdash; explicit JOIN relationships, no guessing</li>
                <li><strong>Centrality Scores</strong> &mdash; most-connected tables highlighted</li>
                <li><strong>[SAFETY] Guardrails</strong> &mdash; blocks sensitive column access and audit table mutation</li>
                <li><strong>Candidate FK Detection</strong> &mdash; inferred missing relationships from naming patterns</li>
            </ul>

            <h2>Token Cost Savings on {db['name']} Schemas</h2>
            <p>Raw {db['short']} DDL dumps run 15,000&ndash;80,000 tokens. Schemap reduces that by <strong>89%%</strong>. Run <code>schemap benchmark --cost</code> to calculate your exact monthly savings.</p>

            <h2>Keep Context in Sync Automatically</h2>
            <div class="terminal" style="margin:16px 0;">
                <div class="terminal-bar"><span style="color:var(--subtle);font-size:.75rem;">bash</span></div>
                <div class="terminal-body" style="padding:16px 20px;"><pre style="margin:0;font-size:.9rem;"><code>schemap hook install
# Auto-regenerates {agent['file']} on every migration commit</code></pre></div>
            </div>

            <hr style="margin:48px 0;border:none;border-top:1px solid var(--line);">

            <h2>Frequently Asked Questions</h2>
            <details style="margin-bottom:16px;border:1px solid var(--line);border-radius:var(--radius);padding:0 16px;">
                <summary style="cursor:pointer;font-weight:600;padding:16px 0;">{faq1_q}</summary>
                <p style="margin:0 0 16px;color:var(--muted);">{faq1_a}</p>
            </details>
            <details style="margin-bottom:16px;border:1px solid var(--line);border-radius:var(--radius);padding:0 16px;">
                <summary style="cursor:pointer;font-weight:600;padding:16px 0;">{faq2_q}</summary>
                <p style="margin:0 0 16px;color:var(--muted);">{faq2_a}</p>
            </details>
            <details style="margin-bottom:16px;border:1px solid var(--line);border-radius:var(--radius);padding:0 16px;">
                <summary style="cursor:pointer;font-weight:600;padding:16px 0;">{faq3_q}</summary>
                <p style="margin:0 0 16px;color:var(--muted);">{faq3_a}</p>
            </details>

            <hr style="margin:48px 0;border:none;border-top:1px solid var(--line);">
            <div style="background:var(--surface2);border:1px solid var(--line);border-radius:var(--radius);padding:32px;text-align:center;">
                <h3 style="margin-top:0;">Ready to give {agent['name']} accurate {db['name']} context?</h3>
                <p style="color:var(--muted);">Free for up to 100 tables. No cloud sync. Schema stays local.</p>
                <a class="btn btn-primary" href="index.html#installation">Install Schemap Free</a>
            </div>
        </article>
    </main>
    <footer style="border-top:1px solid var(--line);padding:40px 24px;text-align:center;color:var(--muted);font-size:.85rem;">
        <p>
            <a href="index.html" style="color:var(--muted);margin:0 12px;">Home</a>
            <a href="docs.html" style="color:var(--muted);margin:0 12px;">Docs</a>
            <a href="blog.html" style="color:var(--muted);margin:0 12px;">Blog</a>
            <a href="security.html" style="color:var(--muted);margin:0 12px;">Security</a>
            <a href="https://github.com/alansyahmi/Schemap" target="_blank" rel="noopener" style="color:var(--muted);margin:0 12px;">GitHub</a>
        </p>
        <p style="margin-top:12px;">&copy; {YEAR} Schemap. Local-first. No cloud sync.</p>
    </footer>
</body>
</html>
"""

def update_sitemap(new_urls):
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_entries = []
    for url in new_urls:
        if url not in content:
            new_entries.append(SITEMAP_ENTRY.format(loc=url, lastmod=TODAY))
    if not new_entries:
        print("  sitemap.xml: no new URLs needed.")
        return
    content = content.replace("</urlset>", "\n".join(new_entries) + "\n</urlset>")
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  sitemap.xml: added {len(new_entries)} URLs.")

def main():
    generated_urls, gen, skip = [], 0, 0
    for db in DATABASES:
        for agent in AGENTS:
            slug = f"for-{db['slug']}-{agent['slug']}"
            out_path = os.path.join(DOCS_DIR, f"{slug}.html")
            url = f"https://schemap-tool.pages.dev/{slug}.html"
            if os.path.exists(out_path):
                print(f"  SKIP  {slug}.html"); skip += 1
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(build_page(db, agent))
                print(f"  GEN   {slug}.html"); gen += 1
            generated_urls.append(url)
    update_sitemap(generated_urls)
    print(f"\nDone. Generated: {gen}  Skipped: {skip}  Total: {len(generated_urls)}")

if __name__ == "__main__":
    main()
