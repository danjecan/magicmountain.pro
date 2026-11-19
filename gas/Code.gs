/**
 * Magic Mountain sign-up and invoice-details backend (Google Apps Script web app).
 *
 * Two things arrive here by POST from the website:
 *
 *   1. A SIGN-UP (the form at /sign-up/). In this order:
 *        - bot checks: honeypot, minimum fill time, optional Cloudflare Turnstile,
 *          and server-side validation of every field;
 *        - a row in the "Bookings" tab of the Google Sheet this script is attached to
 *          (always first, so a sign-up is never lost if Notion is down);
 *        - the person is found or created in the Notion "Customers" database (matched
 *          by email, so a returning family is recognised) and a row is created in the
 *          Notion "Sign-ups" database, linked to the hike and to the customer;
 *        - an email to the organisers.
 *
 *   2. INVOICE DETAILS (the page /invoice/?c=TOKEN). The token in the link belongs to
 *      exactly one Customer. The details are saved on that Customer row, so they are
 *      asked for once and reused for every later hike.
 *
 * Sending the invoice-details link is up to you. In Notion, set a booking's
 * "Invoice link" to Send. A time-driven trigger runs sendInvoiceLinks() every few
 * minutes, emails the link to the people marked Send, and sets them to Sent. If the
 * customer's details are already on file it sets the booking to "On file" instead and
 * sends nothing.
 *
 * Setup (the repo's private setup notes have the full walkthrough):
 *   1. In the Google Sheet: Extensions > Apps Script, paste this file in as Code.gs.
 *   2. Project Settings > Script Properties. Add:
 *        NOTION_TOKEN      secret of a Notion internal integration with "Read content",
 *                          "Update content" and "Insert content", connected ONLY to the
 *                          Sign-ups, Customers and Hikes databases (not the site-build token)
 *        SIGNUPS_DB_ID     41cb4090-01b7-8162-9774-e5b4eabd31c6
 *        CUSTOMERS_DB_ID   41db4090-01b7-81fd-bcb7-d9d60d2bb4d5
 *        HIKES_DB_ID       0a12493f-74f6-4b79-838b-88d3ecbb6512
 *        TURNSTILE_SECRET  optional; Cloudflare Turnstile secret key
 *        NOTIFY_EMAIL      optional; where to send the organiser notifications
 *        SITE_URL          optional; defaults to https://magicmountain.pro
 *   3. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone.
 *   4. Put the web app URL in the GitHub repo variable GAS_SIGNUP_URL.
 *   5. Triggers (clock icon in the left bar) > Add Trigger: function sendInvoiceLinks,
 *      event source Time-driven, type Minutes timer, every 10 minutes.
 *   6. After editing this file: Deploy > Manage deployments > pencil > Version: New
 *      version > Deploy. Editing the script does not update a live deployment by itself.
 *
 * Secrets live in Script Properties, never in this file: the repo is public.
 *
 * The site reads this script's JSON reply. Honeypot and too-fast submissions get
 * {ok:true} on purpose, so bots learn nothing; every other refusal says why.
 */

var HONEYPOT_FIELD = "company_website"; // must match GAS_HONEYPOT_FIELD in the site build
var SHEET_BOOKINGS = "Bookings";
var SHEET_INVOICE = "Invoice details";
var MIN_FILL_MS = 4000; // a human cannot fill these forms in under four seconds
var NOTION_VERSION = "2022-06-28";

var ROOMS = ["One room for the whole family", "Separate rooms", "Not sure yet"];
var FITNESS = { "<3h": "Under 3 hours", "3-6h": "3-6 hours", "6-8h": "6-8 hours", "8h+": "8+ hours", "none": "Haven't done one yet" };
var KIDS_WALK = { "<2h": "Up to 2 hours", "2-4h": "2-4 hours", "4h+": "4+ hours", "unsure": "Not sure" };

var BOOKING_COLUMNS = [
  "Timestamp", "Language", "Hike slug", "Adults", "Children", "Child ages",
  "Name", "Email", "Phone", "Travelling from", "Rooms wanted", "Beds needed",
  "Adult fitness", "Kids longest walk", "Carrying a small child", "Health follow-up",
  "Notes", "Agreed terms", "Agreed privacy", "Page URL", "Notion",
];
var INVOICE_COLUMNS = [
  "Timestamp", "Customer email", "Customer name", "Billing name", "Company", "Tax number",
  "Country", "Postcode", "City", "Street",
];

// ───────────── entry point ─────────────

function doPost(e) {
  var p = (e && e.parameter) || {};
  return p.action === "invoice" ? handleInvoice_(p) : handleSignup_(p, false);
}

// ───────────── sign-up ─────────────

// skipBotCheck is only ever true when testSignup() calls this from the editor; the web
// endpoint (doPost) always runs the Turnstile check and the duplicate guard.
function handleSignup_(p, skipBotCheck) {
  try {
    // Silent drops: look like success to the sender, but are logged (View > Executions).
    if (p[HONEYPOT_FIELD]) { console.log("dropped: honeypot filled"); return reply_(true); }
    if (!(Number(p.form_ms) >= MIN_FILL_MS)) { console.log("dropped: filled in too fast (" + p.form_ms + " ms)"); return reply_(true); }

    var problem = validateSignup_(p);
    if (problem) { console.log("rejected: " + problem); return reply_(false, problem); }

    // Reported (not silent): a real visitor whose security check failed should be told.
    if (!skipBotCheck && !turnstileOk_(p)) { console.log("rejected: Turnstile check failed or missing"); return reply_(false, "bot check failed"); }

    // The same person sending the same hike twice within ten minutes is a double click.
    // (testSignup() skips this guard, so it can be run again straight away.)
    if (!skipBotCheck) {
      var cache = CacheService.getScriptCache();
      var dupKey = "dup:" + p.email.toLowerCase() + ":" + p.hike_slug;
      if (cache.get(dupKey)) { console.log("dropped: duplicate within ten minutes"); return reply_(true); }
      cache.put(dupKey, "1", 600);
    }

    var s = cleanSignup_(p);
    var health = s.health_flag === "Yes" ? "Needed" : "None";

    // Is the hike real? If Notion can't be reached we accept the sign-up anyway.
    var hike = findHike_(s.hike_slug);
    if (hike.status === "missing") { console.log("rejected: unknown hike " + s.hike_slug); return reply_(false, "unknown hike"); }

    var row = [
      new Date(), s.page_lang, s.hike_slug, s.adults, s.children, s.child_ages,
      s.name, s.email, s.phone, s.from_where, s.rooms_pref, s.beds_needed,
      FITNESS[s.fitness] || "", KIDS_WALK[s.kids_walk] || "", s.carry_child, health,
      s.notes, s.agree_terms ? "yes" : "no", s.agree_privacy ? "yes" : "no", s.page_url, "",
    ];

    // 1) Sheet first: the sign-up must never be lost.
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    var sheet = getOrCreateSheet_(SHEET_BOOKINGS, BOOKING_COLUMNS);
    sheet.appendRow(row.map(sheetSafe_));
    var rowNumber = sheet.getLastRow();
    lock.releaseLock();

    // 2) Notion: customer, then the booking.
    var notion = "skipped";
    try {
      var customer = findOrCreateCustomer_(s);
      createBookingRow_(s, hike.id, health, customer);
      notion = "created" + (customer.created ? " (new customer)" : " (returning customer)");
    } catch (err) {
      notion = "FAILED: " + String(err).slice(0, 200);
      console.error("Notion write failed: " + err);
    }
    sheet.getRange(rowNumber, BOOKING_COLUMNS.length).setValue(notion);

    // 3) Email the organisers.
    var to = prop_("NOTIFY_EMAIL");
    if (to) {
      var lines = BOOKING_COLUMNS.map(function (c, i) { return c + ": " + row[i]; });
      lines[BOOKING_COLUMNS.length - 1] = "Notion: " + notion;
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

function validateSignup_(p) {
  var required = ["name", "email", "phone", "hike_slug", "rooms_pref"];
  for (var i = 0; i < required.length; i++) {
    if (!p[required[i]] || !String(p[required[i]]).trim()) return "missing " + required[i];
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(p.email)) return "bad email";
  var adults = Number(p.adults), children = Number(p.children || 0), beds = Number(p.beds_needed);
  if (!(adults >= 1 && adults <= 20) || !(children >= 0 && children <= 20)) return "bad group size";
  if (!(beds >= 1 && beds <= 30)) return "bad beds_needed";
  if (ROOMS.indexOf(p.rooms_pref) === -1) return "bad rooms_pref";
  if (children > 0) {
    // One age per child, e.g. "7, 9". Anyone 18 or older must be entered as an adult.
    var ages = String(p.child_ages || "").split(",").map(function (a) { return a.trim(); });
    if (ages.length !== children) return "child_ages must list one age per child";
    for (var a = 0; a < ages.length; a++) {
      if (!/^\d{1,2}$/.test(ages[a]) || Number(ages[a]) > 17) return "child age must be 0 to 17";
    }
  }
  if (p.health_flag !== "Yes" && p.health_flag !== "No") return "missing health answer";
  if (!p.agree_terms || !p.agree_privacy) return "terms not accepted";
  return lengthsOk_(p);
}

function cleanSignup_(p) {
  var out = {};
  Object.keys(p).forEach(function (k) { out[k] = String(p[k]).trim(); });
  out.email = out.email.toLowerCase();
  out.adults = Number(p.adults);
  out.children = Number(p.children || 0);
  out.beds_needed = Number(p.beds_needed);
  out.page_lang = out.page_lang === "hu" ? "hu" : "en";
  return out;
}

// ───────────── invoice details ─────────────

function handleInvoice_(p) {
  try {
    if (p[HONEYPOT_FIELD]) { console.log("dropped: honeypot filled (invoice)"); return reply_(true); }
    if (!(Number(p.form_ms) >= MIN_FILL_MS)) { console.log("dropped: invoice form too fast (" + p.form_ms + " ms)"); return reply_(true); }

    var token = String(p.token || "").trim();
    if (!/^[0-9a-f-]{36}$/.test(token)) return reply_(false, "invalid link");
    var required = ["country", "postcode", "city", "street"];
    for (var i = 0; i < required.length; i++) {
      if (!p[required[i]] || !String(p[required[i]]).trim()) return reply_(false, "missing " + required[i]);
    }
    var tooLong = lengthsOk_(p);
    if (tooLong) return reply_(false, tooLong);
    if (!turnstileOk_(p)) { console.log("rejected: Turnstile check failed or missing (invoice)"); return reply_(false, "bot check failed"); }

    var found = notion_("POST", "/databases/" + prop_("CUSTOMERS_DB_ID") + "/query", {
      filter: { property: "Invoice token", rich_text: { equals: token } }, page_size: 1,
    });
    if (!found.results.length) { console.log("rejected: unknown invoice token"); return reply_(false, "invalid link"); }
    var customer = found.results[0];

    var d = {};
    Object.keys(p).forEach(function (k) { d[k] = String(p[k]).trim(); });
    notion_("PATCH", "/pages/" + customer.id, { properties: {
      "Billing name": text_(d.billing_name),
      "Company": text_(d.company),
      "Tax number": text_(d.tax_number),
      "Country": text_(d.country),
      "Postcode": text_(d.postcode),
      "City": text_(d.city),
      "Street": text_(d.street),
      "Details": select_("On file"),
      "Details updated": { date: { start: Utilities.formatDate(new Date(), "UTC", "yyyy-MM-dd") } },
    } });

    // Bookings that were waiting for these details are now done.
    var waiting = notion_("POST", "/databases/" + prop_("SIGNUPS_DB_ID") + "/query", {
      filter: { and: [
        { property: "Customer", relation: { contains: customer.id } },
        { property: "Invoice link", select: { equals: "Sent" } },
      ] },
    });
    waiting.results.forEach(function (r) {
      notion_("PATCH", "/pages/" + r.id, { properties: { "Invoice link": select_("On file") } });
    });

    var name = plain_(customer.properties["Name"].title);
    var email = customer.properties["Email"].email || "";

    // Backup copy in the Sheet, then tell the organisers.
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    getOrCreateSheet_(SHEET_INVOICE, INVOICE_COLUMNS).appendRow([
      new Date(), email, name, d.billing_name, d.company, d.tax_number, d.country, d.postcode, d.city, d.street,
    ].map(sheetSafe_));
    lock.releaseLock();

    var to = prop_("NOTIFY_EMAIL");
    if (to) {
      MailApp.sendEmail({ to: to, subject: "Invoice details received: " + name,
        body: "Invoice details received from " + name + " (" + email + "). They are saved on the Customer row in Notion." });
    }
    return reply_(true);
  } catch (err) {
    console.error(err);
    return reply_(false, String(err));
  }
}

// ───────────── sending invoice links (time-driven trigger) ─────────────

function sendInvoiceLinks() {
  var site = prop_("SITE_URL") || "https://magicmountain.pro";
  var queue = notion_("POST", "/databases/" + prop_("SIGNUPS_DB_ID") + "/query", {
    filter: { property: "Invoice link", select: { equals: "Send" } }, page_size: 50,
  });
  queue.results.forEach(function (booking) {
    try {
      var rel = booking.properties["Customer"].relation;
      if (!rel.length) { console.log("skipped: booking " + booking.id + " has no Customer"); return; }
      var customer = notion_("GET", "/pages/" + rel[0].id);
      var cp = customer.properties;

      if (cp["Details"].select && cp["Details"].select.name === "On file") {
        notion_("PATCH", "/pages/" + booking.id, { properties: { "Invoice link": select_("On file") } });
        console.log("details already on file for " + plain_(cp["Name"].title));
        return;
      }

      var token = plain_(cp["Invoice token"].rich_text);
      if (!token) {
        token = Utilities.getUuid();
        notion_("PATCH", "/pages/" + customer.id, { properties: { "Invoice token": text_(token) } });
      }
      var lang = cp["Language"].select && cp["Language"].select.name === "hu" ? "hu" : "en";
      var name = plain_(cp["Name"].title);
      var email = cp["Email"].email;
      if (!email) { console.log("skipped: customer has no email"); return; }

      var hikeTitle = "";
      try {
        var hr = booking.properties["Hike"].relation;
        if (hr.length) {
          var hike = notion_("GET", "/pages/" + hr[0].id);
          hikeTitle = plain_(hike.properties[lang === "hu" ? "Title HU" : "Title EN"].rich_text);
        }
      } catch (e) { /* the email works without the hike title */ }

      var link = site + (lang === "hu" ? "/hu" : "") + "/invoice/?c=" + token;
      var mail = invoiceEmail_(lang, name, hikeTitle, link);
      MailApp.sendEmail({ to: email, subject: mail.subject, body: mail.body, name: "Magic Mountain" });
      notion_("PATCH", "/pages/" + booking.id, { properties: { "Invoice link": select_("Sent") } });
      console.log("invoice link sent to " + name);
    } catch (err) {
      console.error("invoice link failed for " + booking.id + ": " + err);
    }
  });
}

function invoiceEmail_(lang, name, hike, link) {
  if (lang === "hu") {
    return {
      subject: "Számlázási adataid" + (hike ? " – " + hike : "") + " – Magic Mountain",
      body: "Szia " + name + "!\n\nKöszönjük a jelentkezést" + (hike ? " erre a túrára: " + hike : "") + ". " +
        "A számla elkészítéséhez kérjük, add meg a számlázási adataidat az alábbi oldalon (egy perc az egész):\n\n" + link +
        "\n\nEz a link személyes, kérjük, ne oszd meg másokkal. Ha már megadtad ezeket az adatokat, vagy kérdésed van, " +
        "válaszolj erre a levélre.\n\nMagic Mountain",
    };
  }
  return {
    subject: "Your invoice details" + (hike ? " for " + hike : "") + " – Magic Mountain",
    body: "Hi " + name + ",\n\nThank you for signing up" + (hike ? " for " + hike : "") + ". " +
      "To prepare your invoice, please fill in your billing details on this page (it takes a minute):\n\n" + link +
      "\n\nThis link is personal, so please don't share it. If you have already sent us these details, or if you have a " +
      "question, just reply to this email.\n\nMagic Mountain",
  };
}

// ───────────── shared checks ─────────────

function lengthsOk_(p) {
  var keys = Object.keys(p);
  for (var k = 0; k < keys.length; k++) {
    // The Turnstile token is long (well over 1,000 characters), so it gets its own limit.
    var max = keys[k] === "notes" ? 1500 : keys[k] === "cf-turnstile-response" ? 4096 : 300;
    if (String(p[keys[k]]).length > max) return "field too long: " + keys[k];
  }
  return "";
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

// A cell that starts with = + - @ would be read by Sheets as a formula.
function sheetSafe_(v) {
  return (typeof v === "string" && /^[=+\-@]/.test(v)) ? "'" + v : v;
}

// ───────────── Notion ─────────────

function notion_(method, path, body) {
  var opts = {
    method: method,
    headers: { Authorization: "Bearer " + prop_("NOTION_TOKEN"), "Notion-Version": NOTION_VERSION },
    muteHttpExceptions: true,
  };
  if (body) { opts.contentType = "application/json"; opts.payload = JSON.stringify(body); }
  var res = UrlFetchApp.fetch("https://api.notion.com/v1" + path, opts);
  var code = res.getResponseCode();
  if (code < 200 || code >= 300) throw new Error("Notion " + code + " " + res.getContentText().slice(0, 200));
  return JSON.parse(res.getContentText());
}

function text_(v) { return { rich_text: v ? [{ text: { content: String(v).slice(0, 1900) } }] : [] }; }
function select_(v) { return v ? { select: { name: v } } : { select: null }; }
function plain_(rt) { return (rt || []).map(function (t) { return t.plain_text || ""; }).join(""); }

// {status: "found", id} | {status: "missing"} | {status: "unavailable"}
function findHike_(slug) {
  if (!prop_("NOTION_TOKEN") || !prop_("HIKES_DB_ID")) return { status: "unavailable" };
  try {
    var r = notion_("POST", "/databases/" + prop_("HIKES_DB_ID") + "/query", {
      filter: { property: "Slug", rich_text: { equals: slug } },
      page_size: 1,
    });
    return r.results.length ? { status: "found", id: r.results[0].id } : { status: "missing" };
  } catch (err) {
    console.error("Hike lookup failed: " + err);
    return { status: "unavailable" };
  }
}

// Returns {id, onFile, created}. Customers are matched by (lower-case) email.
function findOrCreateCustomer_(s) {
  if (!prop_("NOTION_TOKEN") || !prop_("CUSTOMERS_DB_ID")) throw new Error("Notion not configured");
  var found = notion_("POST", "/databases/" + prop_("CUSTOMERS_DB_ID") + "/query", {
    filter: { property: "Email", email: { equals: s.email } }, page_size: 1,
  });
  if (found.results.length) {
    var c = found.results[0];
    return { id: c.id, onFile: !!(c.properties["Details"].select && c.properties["Details"].select.name === "On file"), created: false };
  }
  var made = notion_("POST", "/pages", {
    parent: { database_id: prop_("CUSTOMERS_DB_ID") },
    properties: {
      "Name": { title: [{ text: { content: s.name.slice(0, 200) } }] },
      "Email": { email: s.email },
      "Language": select_(s.page_lang),
      "Details": select_("Missing"),
      "Invoice token": text_(Utilities.getUuid()),
    },
  });
  return { id: made.id, onFile: false, created: true };
}

function createBookingRow_(s, hikeId, health, customer) {
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
    "Rooms wanted": select_(s.rooms_pref),
    "Beds needed": { number: s.beds_needed },
    "Adult fitness": text_(FITNESS[s.fitness] || ""),
    "Kids longest walk": text_(KIDS_WALK[s.kids_walk] || ""),
    "Carrying a small child": select_(s.carry_child === "Yes" || s.carry_child === "No" ? s.carry_child : ""),
    "Health follow-up": select_(health),
    "Notes": text_(s.notes),
    "Language": select_(s.page_lang),
    "Agreed terms": { checkbox: !!s.agree_terms },
    "Agreed privacy": { checkbox: !!s.agree_privacy },
    "Customer": { relation: [{ id: customer.id }] },
    "Invoice link": select_(customer.onFile ? "On file" : "Not yet"),
  };
  if (s.page_url && /^https:\/\//.test(s.page_url)) props["Page URL"] = { url: s.page_url.slice(0, 1900) };
  if (hikeId) props["Hike"] = { relation: [{ id: hikeId }] };
  notion_("POST", "/pages", { parent: { database_id: prop_("SIGNUPS_DB_ID") }, properties: props });
}

// ───────────── helpers ─────────────

function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k) || ""; }

function getOrCreateSheet_(name, columns) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(columns);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function reply_(ok, error) {
  var obj = ok ? { ok: true } : { ok: false, error: error || "error" };
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Run this once from the Apps Script editor (Run > testSignup) to check the whole chain
// before pointing the site at the deployment. It writes a clearly labelled TEST booking
// (and a TEST customer). Delete both afterwards. It skips the Turnstile check.
function testSignup() {
  var res = handleSignup_({
    form_ms: "60000", page_lang: "en", hike_slug: "aggtelek-2027-03", adults: "2", children: "1",
    child_ages: "7", name: "TEST Please Delete", email: "test@example.com", phone: "+36 30 000 0000",
    from_where: "Budapest", rooms_pref: "One room for the whole family", beds_needed: "3",
    kids_walk: "2-4h", carry_child: "No", health_flag: "No", notes: "test", agree_terms: "on",
    agree_privacy: "on", page_url: "https://magicmountain.pro/sign-up/",
  }, true);
  console.log("Result: " + res.getContent());
}
