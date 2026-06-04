# Setup walkthrough — GitHub → Cloudflare Pages

This is a one-time setup. After it's done, every push to GitHub auto-deploys
to your Cloudflare Pages site. Allow about 15 minutes.

## Step 1 — Create the GitHub repo (≈ 3 min)

1. Go to https://github.com/new
2. Owner: `negumbojoshua-del`
3. Repository name: **`justina-jonas-site`** (or anything you prefer —
   just remember it)
4. Visibility: **Public**
5. Leave "Add a README" / .gitignore / license **unchecked** — we already
   have those files locally.
6. Click **Create repository**.

You'll land on an empty repo page with instructions. Ignore them; we'll
upload via the web UI in the next step.

## Step 2 — Upload the three files (≈ 2 min)

1. On the empty repo page, click the **"uploading an existing file"** link
   (or click the **Add file** dropdown → **Upload files**).
2. Drag in **all three files** from your `outputs/repo` folder:
   - `index.html`
   - `README.md`
   - `.gitignore`
3. At the bottom, the commit message will default to "Add files via upload".
   Leave it, click **Commit changes**.
4. The upload of `index.html` will take 30–90 seconds because the file is
   ~8.3 MB. Wait until GitHub shows the repo tree with all three files.

> **Note:** GitHub's web uploader has a 25 MB per-file limit, so index.html
> fits comfortably. If you ever embed bigger media, switch to `git push`
> from your computer instead.

## Step 3 — Connect Cloudflare Pages to the repo (≈ 5 min)

1. Open the Cloudflare dashboard → **Workers & Pages** in the left sidebar.
2. Find your existing Pages project (the one currently behind your
   `*.pages.dev` preview link) and click into it.
3. Go to **Settings → Builds & deployments → Source**.
4. If it currently says "Direct Upload":
   - Click **Connect to Git** (or **Reconnect** / **Change**).
   - Authorise Cloudflare to access your GitHub account when prompted.
   - Pick the repo `negumbojoshua-del/justina-jonas-site`.
   - Production branch: **`main`**.
   - Build command: **leave empty**.
   - Build output directory: **`/`** (just a forward slash).
5. Save. Cloudflare will run an initial deploy. Watch the **Deployments**
   tab — it should go ✅ green in ~30 seconds (no build step, just a
   file copy).

If you can't switch the existing project from Direct Upload → Git in the
UI, the alternative is:
- **Create → Pages → Connect to Git → pick the repo → Deploy.** This makes
  a *new* `pages.dev` URL. Then in the **Custom domains** tab of the new
  project, attach the same domain you were going to use. Delete the old
  project once everything works.

## Step 4 — Test the auto-deploy loop (≈ 2 min)

1. In GitHub, click `README.md` → ✏️ pencil → add a line at the bottom
   (anything, e.g. "Test deploy") → **Commit changes**.
2. In Cloudflare → **Deployments**, you should see a new deployment kick
   off within 10 seconds and finish in under a minute.
3. Open your `*.pages.dev` URL and refresh. The site should look unchanged
   (because we only edited the README), confirming nothing broke.

You're done. From now on:
- **To update content manually:** edit `index.html` in GitHub (or push from
  your computer), Cloudflare auto-deploys.
- **The Facebook live feed (Latest Updates section)** continues to update on
  its own from her Page — no GitHub push needed for that.

## Step 5 (optional, later) — Add scheduled auto-refresh

Once everything above works, ask Claude in Cowork to add the GitHub Actions
workflow that scrapes Hon. Jonas's FB Page weekly, regenerates the Recent
Highlights / Recent Sessions cards, and commits the changes — so the
editorial layer auto-updates too. We'll add `.github/workflows/refresh.yml`
at that point.

## What to do if you get stuck

Paste the error or screenshot back into Cowork and I'll help debug it.
The two most common snags:
1. **Cloudflare can't find the repo** — go back to GitHub, **Settings →
   Applications → Authorised OAuth Apps** and make sure Cloudflare has
   access.
2. **Deployment shows the wrong content** — confirm the Production branch
   in Cloudflare is `main` and that `index.html` sits at the *root* of the
   repo (not inside a `repo/` folder).
