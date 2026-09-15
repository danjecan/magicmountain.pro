# magicmountain.pro

The Magic Mountain website: a static site built from the design in
[magic-mountain-design](https://github.com/danjecan/magic-mountain-design), published
to [magicmountain.pro](https://magicmountain.pro) via GitHub Pages. English and
Hungarian, hike pages generated from the Notion Hikes database, a sign-up form to
Google Apps Script, and a Mailchimp newsletter with double opt-in.

## How it's built

There is no client-side framework and nothing is stored server-side except a Google
Sheet (sign-ups) and Mailchimp (the newsletter list). A Python script (stdlib only,
no dependencies to install) generates plain HTML at build time:

```
src/
  build.py          entry point — run this to build the site
  notion_source.py  talks to the Notion API, turns Hikes rows into Hike objects
  content.py        every fixed piece of copy, English/Hungarian pairs
  config.py         reads the sign-up/newsletter endpoints from env vars
  layout.py         <head>, nav, footer, the icon set
  components.py     buttons, tags, cards, form fields, bands
  hikes_render.py   hike card + hike detail page rendering
  pages.py          home, hike list, about, sign-up, terms, 404
  seo.py            sitemap.xml / robots.txt
  util.py           slugs, date/money formatting

assets/
  css/site.css      the whole stylesheet (design tokens ported from the design repo)
  fonts/            Archivo + Source Sans 3, self-hosted (no Google Fonts at runtime)
  img/              logo + stock photography from the design
  js/main.js        mobile nav, quantity steppers, sign-up + newsletter form handling

gas/Code.gs         Google Apps Script backend for the sign-up form (paste into script.google.com)
.github/workflows/deploy.yml   builds and deploys to GitHub Pages
```

Build locally:

```
python3 src/build.py        # writes the site into ./dist
python3 -m http.server -d dist 8000
```

Without `NOTION_TOKEN` set, the build still works — it just produces zero hikes, so
you'll see the site's "no hikes yet" empty states (a real state the site can be in).

## One-time setup before this actually works end-to-end

Everything below is a manual step outside this repo. Nothing here holds a secret —
they're all supplied as GitHub Actions secrets/variables at build time.

### 1. GitHub Pages

Repo Settings → Pages → Source: **GitHub Actions**. The workflow
(`.github/workflows/deploy.yml`) builds and deploys on every push to `main`, on a
daily schedule (to catch Notion edits even without a push), and on demand.

Custom domain: enter `magicmountain.pro` in the same Pages settings screen (the
build already writes a `CNAME` file, but GitHub also needs it entered in the UI to
provision HTTPS). At your domain registrar, point the apex domain at GitHub Pages:

```
A     @     185.199.108.153
A     @     185.199.109.153
A     @     185.199.110.153
A     @     185.199.111.153
```

(or a `CNAME`/`ALIAS`/`ANAME` record at the apex to `<username>.github.io` if your
DNS provider supports it). Wait for the Pages settings screen to show the padlock/
"Enforce HTTPS" checkbox available, then enable it.

### 2. Notion (hike content)

The site reads the **Hikes** database (Personal → Magic Mountain → Hikes in Notion).
Its schema and the per-hike content contract (the exact `## What this one is like` /
`## Day by day` / `### Day 1 · Title · stats` headings) are already set up — see the
"TEMPLATE – copy me for each new hike" page in that database for the format
`notion_source.py` parses. Only rows with **Published** ticked and a **Status** of
Upcoming, Full, or Past appear on the site; Draft and Cancelled never do.

To let the build read it:

1. In Notion, go to **Settings → Connections → Develop or manage integrations** and
   create a new **internal integration** scoped to your workspace (read-only content
   capability is enough). Copy its secret.
2. Open the Hikes database → `···` menu → **Connections** → add that integration, so
   it's allowed to read the database.
3. In the GitHub repo, add a secret **`NOTION_TOKEN`** with that integration secret.
4. (Only if you ever recreate the database) add a repo variable
   **`NOTION_DATABASE_ID`** with its ID — the build defaults to the current Hikes
   database, so this is optional today.

Cover images and photos are downloaded at build time from Notion's signed URLs (which
expire quickly) into `assets/img/hikes/<slug>/`, so the published site never links
back to Notion for images.

### 3. Sign-up form → Google Apps Script

1. Create a Google Sheet (e.g. "Magic Mountain sign-ups") in the Magic Mountain
   Google account.
2. Extensions → Apps Script, delete the placeholder code, paste in `gas/Code.gs`.
3. Deploy → New deployment → type **Web app** → Execute as **Me**, who has access
   **Anyone**. Authorize it when prompted (it's your own script).
4. Copy the resulting web app URL.
5. In the GitHub repo, add a repo variable **`GAS_SIGNUP_URL`** with that URL. (If
   you changed `HONEYPOT_FIELD` in Code.gs away from the default, also add
   **`GAS_HONEYPOT_FIELD`** with the matching name — the site and the script must
   agree on it.)

The sign-up form includes a hidden honeypot field real visitors never see or fill;
if it arrives filled in, the script silently discards the submission. Sign-ups land
as rows in the "Sign-ups" sheet tab (created automatically on first submission), and
optionally email a notification — see `NOTIFY_EMAIL` in Code.gs.

### 4. Newsletter → Mailchimp (double opt-in)

1. In Mailchimp, create (or reuse) an **Audience**. Under Audience → Settings →
   Audience name and defaults, and under **Signup forms → Form builder**, make sure
   **double opt-in** is turned on (Audience → Settings → Audience fields & \*|MERGE|\*
   tags, and the "Enable double opt-in" toggle under Signup forms settings) — this is
   a list-level setting, not something the site's HTML controls.
2. Go to **Audience → Signup forms → Embedded forms**, pick the classic/naked style,
   and read off three values from the generated code: the form's `action` URL
   (`https://xxxx.usN.list-manage.com/subscribe/post`), and the hidden `u` and `id`
   field values.
3. In the GitHub repo, add repo variables **`MAILCHIMP_ACTION_URL`**,
   **`MAILCHIMP_U`**, **`MAILCHIMP_LIST_ID`** with those three values.

Mailchimp's own hidden bot-trap field (`b_{u}_{id}`) is included automatically once
those are set, as a second layer of spam protection alongside the honeypot pattern
used on the sign-up form.

## Still to fill in before launch

Carried over from the design repo's own "still to fill in" list — search the built
site for `[BRACKETS]`:

- Dates, prices, phone number, years of experience, insurer/policy numbers.
- Photos of Dan and Anett (replacing the `[PHOTO OF DAN/ANETT]` placeholders in
  `src/content.py`, keys `photo_dan` / `photo_anett`).
- The Terms page (`pol1`–`pol8` in `src/content.py`): bank account/IBAN, tax number,
  business address, refund percentages and deadlines — this is a plain-language
  draft, not legal advice, and should be checked before publishing.
- Hungarian copy was written, not machine-translated, but hasn't been proofread by a
  second native speaker.

None of this blocks a build or a deploy — the site renders correctly with the
placeholders in place, exactly as the design intended.
