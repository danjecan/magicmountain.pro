// Magic Mountain — small, dependency-free page behaviour:
// mobile nav, quantity steppers, the sign-up form (Google Apps Script + honeypot),
// and the newsletter form's inline confirmation (Mailchimp, double opt-in).
(function () {
  "use strict";

  // ---- Mobile nav ----
  var navBtn = document.getElementById("navMenuBtn");
  var navMobile = document.getElementById("navMobile");
  if (navBtn && navMobile) {
    navBtn.addEventListener("click", function () {
      var open = navMobile.classList.toggle("open");
      navBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---- Booking bar visibility (phone only, upcoming hike pages) ----
  var bookBar = document.getElementById("bookBar");
  if (bookBar) {
    var toggleBookBar = function () {
      bookBar.classList.toggle("active", window.matchMedia("(max-width: 700px)").matches);
    };
    toggleBookBar();
    window.addEventListener("resize", toggleBookBar);
  }

  // ---- Quantity steppers (adults / children) ----
  document.querySelectorAll(".stepper").forEach(function (group) {
    var output = group.querySelector("output");
    var hidden = group.querySelector('input[type="hidden"]');
    var min = output.id === "adults_count" ? 1 : 0;
    var max = 10;
    function set(v) {
      v = Math.max(min, Math.min(max, v));
      output.textContent = String(v);
      hidden.value = String(v);
    }
    group.querySelectorAll("button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var cur = parseInt(hidden.value, 10) || 0;
        set(cur + (btn.classList.contains("stepper-inc") ? 1 : -1));
      });
    });
  });

  // ---- Pre-fill "which hike" from ?hike=slug ----
  var hikeSelect = document.getElementById("hike_slug");
  if (hikeSelect) {
    var params = new URLSearchParams(window.location.search);
    var wanted = params.get("hike");
    if (wanted) {
      for (var i = 0; i < hikeSelect.options.length; i++) {
        if (hikeSelect.options[i].value === wanted) {
          hikeSelect.selectedIndex = i;
          break;
        }
      }
    }
  }

  // ---- Sign-up form -> Google Apps Script, with a honeypot ----
  var signupForm = document.getElementById("signupForm");
  if (signupForm) {
    signupForm.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var okBox = document.getElementById("signupOk");
      var errBox = document.getElementById("signupErr");
      okBox.hidden = true;
      errBox.hidden = true;

      if (!signupForm.checkValidity()) {
        signupForm.reportValidity();
        return;
      }

      // Honeypot: a real visitor never fills this hidden field. If it's filled,
      // pretend the submission worked (never tell a bot it was caught) and stop.
      var honeypot = signupForm.querySelector('.honeypot-field input[type="text"]');
      if (honeypot && honeypot.value.trim() !== "") {
        okBox.hidden = false;
        signupForm.reset();
        return;
      }

      var submitBtn = signupForm.querySelector('button[type="submit"]');
      var originalLabel = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = submitBtn.getAttribute("data-sending-label") || originalLabel;

      var data = new FormData(signupForm);
      data.append("page_lang", document.documentElement.lang);
      data.append("page_url", window.location.href);

      fetch(window.MM_GAS_URL, {
        method: "POST",
        mode: "no-cors", // Apps Script web apps don't return CORS headers; we can't
        body: data,      // read the response, so treat a resolved fetch as success.
      })
        .then(function () {
          okBox.hidden = false;
          signupForm.reset();
          signupForm.querySelectorAll(".stepper output").forEach(function (o) { o.textContent = o.id === "adults_count" ? "2" : "0"; });
        })
        .catch(function () {
          errBox.hidden = false;
        })
        .finally(function () {
          submitBtn.disabled = false;
          submitBtn.textContent = originalLabel;
        });
    });
  }

  // ---- Newsletter forms -> Mailchimp (double opt-in is a list setting) ----
  document.querySelectorAll("form.mc-embed").forEach(function (form) {
    form.addEventListener("submit", function () {
      // The form still submits natively (target="_blank") so Mailchimp's own
      // subscribe/confirm flow runs normally; this just gives immediate feedback
      // on the page the visitor is still looking at. We can't read the response
      // (cross-origin), so this is optimistic, not a confirmed result.
      var email = form.querySelector('input[type="email"]');
      var okMsg = form.querySelector(".nl-msg-ok");
      var errMsg = form.querySelector(".nl-msg-err");
      errMsg.hidden = true;
      if (email && email.checkValidity() && email.value.trim() !== "") {
        okMsg.hidden = false;
      }
    });
  });
})();
