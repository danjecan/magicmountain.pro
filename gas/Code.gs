/**
 * Magic Mountain sign-up form backend (Google Apps Script web app).
 *
 * What it does with each sign-up, in this order:
 *   1. Rejects bots: honeypot field, a minimum fill time, an optional Cloudflare
 *      Turnstile check, and server-side validation of every field.
 *   2. Appends a row to the "Sign-ups" tab of the Google Sheet this script is attached
 *      to. This always happens first, so a sign-up is never lost if Notion is down.
 *   3. Creates a row in the Notion "Sign-ups" database, linked to the hike's row in the
 *      Notion Hikes database. If this fails the sign-up is still in the Sheet and the
 *      notification email says so.
 *   4. Emails the organisers.
 *
 * Setup (the repo's private setup notes have the full walkthrough):
 *   1. Create a Google Sheet, then Extensions > Apps Script, and paste this file in.
 *   2. Project Settings > Script Properties. Add:
 *        NOTION_TOKEN      secret of a Notion internal integration that has "Insert
 *                          content" + "Read content" and is connected ONLY to the
 *                          Sign-ups and Hikes databases (not the site-build token)
 *        SIGNUPS_DB_ID     41cb4090-01b7-8162-9774-e5b4eabd31c6   (Notion Sign-ups database)
 *        HIKES_DB_ID       0a12493f-74f6-4b79-838b-88d3ecbb6512   (Notion Hikes database)
 *        TURNSTILE_SECRET  optional; Cloudflare Turnstile secret key. Leave unset to
 *                          skip the check (then leave TURNSTILE_SITE_KEY unset in the
 *                          site build too).
 *        NOTIFY_EMAIL      optional; where to send the notification
 *   3. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone.
 *   4. Put the web app URL in the GitHub repo variable GAS_SIGNUP_URL.
 *   5. After editing this file, Deploy > Manage deployments > New version. Editing the
 *      script does not update a live deployment by itself.
 *
 * Secrets live in Script Properties, never in this file: the repo is public.
 *
 * The form posts multipart/form-data via fetch(..., {mode: "no-cors"}), so the
 * browser can't read this script's reply. Every rejection therefore looks like
 * success to the sender, which also means bots learn nothing.
 */

var HONEYPOT_FIELD = "company_website"; // must match GAS_HONEYPOT_FIELD in the site build
var SHEET_NAME = "Sign-ups";
var MIN_FILL_MS = 4000; // a human cannot fill this form in under four seconds
var NOTION_VERSION = "2022-06-28";

var COLUMNS = [
  "Timestamp", "Language", "Hike slug", "Adults", "Children", "Child ages",
  "Name", "Email", "Phone", "Travelling from",
  "Billing name", "Company", "Tax number", "Country", "Postcode", "City", "Street",
  "Adult fitness", "Kids longest walk", "Carrying a small child", "Health follow-up",
  "Notes", "Agreed terms", "Agreed privacy", "Page URL", "Notion",
];

var FITNESS = { "<3h": "Under 3 hours", "3-6h": "3-6 hours", "6-8h": "6-8 hours", "8h+": "8+ hours", "none": "Haven't done one yet" };
var KIDS_WALK = { "<2h": "Up to 2 hours", "2-4h": "2-4 hours", "4h+": "4+ hours", "unsure": "Not sure" };

function doPost(e) {
  return handle_((e && e.parameter) || {}, false);
}

// skipBotCheck is only ever true when testSignup() calls this from the editor; the web
// endpoint (doPost) always runs the Turnstile check.
function handle_(p, skipBotCheck) {
  try {
    // Silent drops: look like success to the sender, but are logged here (View > Executions).
    if (p[HONEYPOT_FIELD]) { console.log("dropped: honeypot filled"); return reply_(true); }
    if (!(Number(p.form_ms) >= MIN_FILL_MS)) { console.log("dropped: filled in too fast (" + p.form_ms + " ms)"); return reply_(true); }

    var problem = validate_(p);
    if (problem) { console.log("rejected: " + problem); return reply_(false, problem); }

    // Reported (not silent): a real visitor whose security check failed should be told.
    if (!skipBotCheck && !turnstileOk_(p)) { console.log("rejected: Turnstile check failed or missing"); return reply_(false, "bot check failed"); }

    // The same person sending the same hike twice within ten minutes is a double
    // click or a retry: record it once.
    var cache = CacheService.getScriptCache();
    var dupKey = "dup:" + p.email.toLowerCase() + ":" + p.hike_slug;
    if (cache.get(dupKey)) { console.log("dropped: duplicate within ten minutes"); return reply_(true); }
    cache.put(dupKey, "1", 600);

    var s = clean_(p);
    var health = s.health_flag === "Yes" ? "Needed" : "None";

    // Is the hike real? If Notion can't be reached we accept the sign-up anyway.
    var hike = findHike_(s.hike_slug);
    if (hike.status === "missing") { console.log("rejected: unknown hike " + s.hike_slug); return reply_(false, "unknown hike"); }

    var notion = "skipped";
    var row = [
      new Date(), s.page_lang, s.hike_slug, s.adults, s.children, s.child_ages,
      s.name, s.email, s.phone, s.from_where,
      s.billing_name, s.company, s.tax_number, s.country, s.postcode, s.city, s.street,
      FITNESS[s.fitness] || "", KIDS_WALK[s.kids_walk] || "", s.carry_child, health,
      s.notes, s.agree_terms ? "yes" : "no", s.agree_privacy ? "yes" : "no", s.page_url, "",
    ];

    // 1) Sheet first: the sign-up must never be lost.
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    var sheet = getOrCreateSheet_();
    sheet.appendRow(row.map(sheetSafe_));
    var rowNumber = sheet.getLastRow();
    lock.releaseLock();

    // 2) Notion.
    try {
      createNotionRow_(s, hike.id, health);
      notion = "created";
    } catch (err) {
      notion = "FAILED: " + String(err).slice(0, 200);
      console.error("Notion write failed: " + err);
    }
    sheet.getRange(rowNumber, COLUMNS.length).setValue(notion);

    // 3) Email.
    var to = prop_("NOTIFY_EMAIL");
    if (to) {
      var lines = COLUMNS.map(function (c, i) { return c + ": " + row[i]; });
      lines[COLUMNS.length - 1] = "Notion: " + notion;
      MailApp.sendEmail({
        to: to,
        subject: (health === "Needed" ? "[HEALTH FOLLOW-UP] " : "") + "New sign-up: " + s.hike_slug + " (" + s.name + ")",
        body: lines.join("\n"),
      });
    }

    return reply_(true);
  } catch (err) {
    console.error(err);
    return reply_(false, String(err));
  }
}

// ───────────── validation ─────────────

function validate_(p) {
  var required = ["name", "email", "phone", "hike_slug", "country", "postcode", "city", "street"];
  for (var i = 0; i < required.length; i++) {
    if (!p[required[i]] || !String(p[required[i]]).trim()) return "missing " + required[i];
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(p.email)) return "bad email";
  var adults = Number(p.adults), children = Number(p.children || 0);
  if (!(adults >= 1 && adults <= 20) || !(children >= 0 && children <= 20)) return "bad group size";
  if (children > 0 && !(p.child_ages && String(p.child_ages).trim())) return "missing child_ages";
  if (p.health_flag !== "Yes" && p.health_flag !== "No") return "missing health answer";
  if (!p.agree_terms || !p.agree_privacy) return "terms not accepted";
  var keys = Object.keys(p);
  for (var k = 0; k < keys.length; k++) {
    // The Turnstile token is long (well over 1,000 characters), so it gets its own limit.
    var max = keys[k] === "notes" ? 1500 : keys[k] === "cf-turnstile-response" ? 4096 : 300;
    if (String(p[keys[k]]).length > max) return "field too long: " + keys[k];
  }
  return "";
}

function clean_(p) {
  var out = {};
  Object.keys(p).forEach(function (k) { out[k] = String(p[k]).trim(); });
  out.adults = Number(p.adults);
  out.children = Number(p.children || 0);
  out.page_lang = out.page_lang === "hu" ? "hu" : "en";
  return out;
}

// A cell that starts with = + - @ would be read by Sheets as a formula.
function sheetSafe_(v) {
  return (typeof v === "string" && /^[=+\-@]/.test(v)) ? "'" + v : v;
}

function turnstileOk_(p) {
  var secret = prop_("TURNSTILE_SECRET");
  if (!secret) return true; // check not configured
  var token = p["cf-turnstile-response"];
  if (!token) return false;
  var res = UrlFetchApp.fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "post",
    payload: { secret: secret, response: token },
    muteHttpExceptions: true,
  });
  try { return JSON.parse(res.getContentText()).success === true; } catch (e) { return false; }
}

// ───────────── Notion ─────────────

function notion_(path, body) {
  var res = UrlFetchApp.fetch("https://api.notion.com/v1" + path, {
    method: "post",
    contentType: "application/json",
    headers: { Authorization: "Bearer " + prop_("NOTION_TOKEN"), "Notion-Version": NOTION_VERSION },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });
  var code = res.getResponseCode();
  if (code < 200 || code >= 300) throw new Error("Notion " + code + " " + res.getContentText().slice(0, 200));
  return JSON.parse(res.getContentText());
}

// {status: "found", id} | {status: "missing"} | {status: "unavailable"}
function findHike_(slug) {
  if (!prop_("NOTION_TOKEN") || !prop_("HIKES_DB_ID")) return { status: "unavailable" };
  try {
    var r = notion_("/databases/" + prop_("HIKES_DB_ID") + "/query", {
      filter: { property: "Slug", rich_text: { equals: slug } },
      page_size: 1,
    });
    return r.results.length ? { status: "found", id: r.results[0].id } : { status: "missing" };
  } catch (err) {
    console.error("Hike lookup failed: " + err);
    return { status: "unavailable" };
  }
}

function text_(v) { return { rich_text: v ? [{ text: { content: String(v).slice(0, 1900) } }] : [] }; }
function select_(v) { return v ? { select: { name: v } } : { select: null }; }

function createNotionRow_(s, hikeId, health) {
  if (!prop_("NOTION_TOKEN") || !prop_("SIGNUPS_DB_ID")) throw new Error("Notion not configured");
  var props = {
    "Name": { title: [{ text: { content: s.name.slice(0, 200) } }] },
    "Status": select_("New"),
    "Adults": { number: s.adults },
    "Children": { number: s.children },
    "Child ages": text_(s.child_ages),
    "Email": { email: s.email },
    "Phone": { phone_number: s.phone },
    "Travelling from": text_(s.from_where),
    "Billing name": text_(s.billing_name),
    "Company": text_(s.company),
    "Tax number": text_(s.tax_number),
    "Country": text_(s.country),
    "Postcode": text_(s.postcode),
    "City": text_(s.city),
    "Street": text_(s.street),
    "Adult fitness": text_(FITNESS[s.fitness] || ""),
    "Kids longest walk": text_(KIDS_WALK[s.kids_walk] || ""),
    "Carrying a small child": select_(s.carry_child === "Yes" || s.carry_child === "No" ? s.carry_child : ""),
    "Health follow-up": select_(health),
    "Notes": text_(s.notes),
    "Language": select_(s.page_lang),
    "Agreed terms": { checkbox: !!s.agree_terms },
    "Agreed privacy": { checkbox: !!s.agree_privacy },
  };
  if (s.page_url && /^https:\/\//.test(s.page_url)) props["Page URL"] = { url: s.page_url.slice(0, 1900) };
  if (hikeId) props["Hike"] = { relation: [{ id: hikeId }] };
  notion_("/pages", { parent: { database_id: prop_("SIGNUPS_DB_ID") }, properties: props });
}

// ───────────── helpers ─────────────

function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k) || ""; }

function getOrCreateSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(COLUMNS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function reply_(ok, error) {
  var obj = ok ? { ok: true } : { ok: false, error: error || "error" };
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Run this once from the Apps Script editor (Run > testSignup) to check the whole chain
// before pointing the site at the deployment. It writes a clearly labelled TEST row.
function testSignup() {
  var res = handle_({
    form_ms: "60000", page_lang: "en", hike_slug: "aggtelek-2027-03", adults: "2", children: "1",
    child_ages: "7", name: "TEST Please Delete", email: "test@example.com", phone: "+36 30 000 0000",
    from_where: "Budapest", country: "Hungary", postcode: "1011", city: "Budapest", street: "Test u. 1",
    kids_walk: "2-4h", carry_child: "No", health_flag: "No", notes: "test", agree_terms: "on",
    agree_privacy: "on", page_url: "https://magicmountain.pro/sign-up/",
  }, true);
  console.log("Result: " + res.getContent());
}
