# Hon. Justina Jonas — Official Site

Static one-page site for Hon. Justina Jonas, Member of Parliament of the Republic of Namibia.

## Deployment
Deployed via Cloudflare Pages, auto-deploying from this repository's `main` branch.
Any push to `main` triggers a fresh build at the configured `*.pages.dev` URL
(and the custom domain once attached).

## Content freshness
- The **Latest Updates** section on the Home page is a live Facebook Page
  Plugin iframe pointed at the official Page
  (`facebook.com/profile.php?id=61566660548678`) and updates automatically
  whenever a new post is published — no rebuild required.
- The **Recent Highlights**, **Recent Sessions & Activity**, and **In the
  News** cards are curated static HTML and are updated manually (or via a
  scheduled GitHub Action — see `.github/workflows/refresh.yml` when added).

## Stack
- Single `index.html` (~8.3 MB; embeds images as base64 to avoid extra
  HTTP requests on first paint)
- Google Fonts: Playfair Display (headings), Lora (quotes), Inter (body)
- Palette: navy `#0d1b2a` / gold `#c9a84c` / cream `#f8f4ed`
- No build step. Just a static file.
