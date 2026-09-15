/**
 * Magic Mountain sign-up form backend.
 *
 * Setup (see README.md for the full walkthrough):
 *   1. Create a Google Sheet named e.g. "Magic Mountain sign-ups".
 *   2. Extensions > Apps Script, paste this whole file in as Code.gs.
 *   3. Set HONEYPOT_FIELD below to match config.py's GAS_HONEYPOT_FIELD
 *      (defaults to "company_website" — leave both at the default unless
 *      you changed one of them).
 *   4. Deploy > New deployment > type "Web app".
 *        Execute as: Me
 *        Who has access: Anyone
 *   5. Copy the deployment's web app URL into the GAS_SIGNUP_URL secret/env
 *      var used by the site build (see README.md).
 *   6. Re-run "Deploy > Manage deployments" and create a new version any
 *      time you edit this file — editing the script does not update a
 *      live deployment by itself.
 *
 * The form posts as multipart/form-data (via the browser's fetch(FormData)),
 * which Apps Script exposes on e.parameter — no JSON parsing needed.
 */

var HONEYPOT_FIELD = "company_website";
var SHEET_NAME = "Sign-ups";
var NOTIFY_EMAIL = "magicmountain.pro@gmail.com"; // set to "" to disable the notification email

var COLUMNS = [
  "Timestamp", "Language", "Hike slug", "Adults", "Children",
  "Name", "Email", "Phone", "Travelling from",
  "Fitness", "Notes", "Agreed to terms", "Agreed to privacy", "Page URL",
];

function doPost(e) {
  try {
    var p = (e && e.parameter) || {};

    // Honeypot: a real visitor never fills this hidden field. If it's
    // filled, silently report success without recording anything.
    if (p[HONEYPOT_FIELD]) {
      return jsonResponse({ ok: true });
    }

    if (!p.email || !p.name || !p.hike_slug) {
      return jsonResponse({ ok: false, error: "missing required field" });
    }

    var sheet = getOrCreateSheet();
    sheet.appendRow([
      new Date(),
      p.page_lang || "",
      p.hike_slug || "",
      p.adults || "",
      p.children || "",
      p.name || "",
      p.email || "",
      p.phone || "",
      p.from_where || "",
      p.fitness || "",
      p.notes || "",
      p.agree_terms ? "yes" : "no",
      p.agree_privacy ? "yes" : "no",
      p.page_url || "",
    ]);

    if (NOTIFY_EMAIL) {
      MailApp.sendEmail({
        to: NOTIFY_EMAIL,
        subject: "New sign-up: " + p.hike_slug + " (" + p.name + ")",
        body: COLUMNS.map(function (c, i) { return c + ": " + (sheet.getRange(sheet.getLastRow(), i + 1).getValue()); }).join("\n"),
      });
    }

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function getOrCreateSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(COLUMNS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function jsonResponse(obj) {
  // The site calls this endpoint with fetch(..., {mode: "no-cors"}) because
  // Apps Script web apps don't send CORS headers, so the browser can't read
  // this response anyway — it only matters that the request completes.
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
