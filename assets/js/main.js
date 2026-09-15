// Magic Mountain — small, dependency-free page behaviour:
// mobile nav, quantity steppers, the sign-up form (Google Apps Script + honeypot),
// and the newsletter form's inline confirmation (Mailchimp, double opt-in).
(function () {
  "use strict";

  // ---- Mobile nav: full-screen sheet ----
  var navBtn = document.getElementById("navMenuBtn");
  var sheet = document.getElementById("navSheet");
  var sheetClose = document.getElementById("navSheetClose");
  if (navBtn && sheet) {
    var openSheet = function () {
      sheet.hidden = false;
      document.body.classList.add("sheet-open");
      navBtn.setAttribute("aria-expanded", "true");
      if (sheetClose) sheetClose.focus();
    };
    var closeSheet = function () {
      sheet.hidden = true;
      document.body.classList.remove("sheet-open");
      navBtn.setAttribute("aria-expanded", "false");
      navBtn.focus();
    };
    navBtn.addEventListener("click", openSheet);
    if (sheetClose) sheetClose.addEventListener("click", closeSheet);
    sheet.addEventListener("click", function (evt) {
      if (evt.target.tagName === "A") closeSheet();
    });
    document.addEventListener("keydown", function (evt) {
      if (evt.key === "Escape" && !sheet.hidden) closeSheet();
    });
  }

  // ---- Parallax hero (desktop only, off for reduced motion) ----
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var parallaxEls = document.querySelectorAll("[data-parallax]");
  if (parallaxEls.length && !reduceMotion) {
    var onScroll = function () {
      if (window.matchMedia("(max-width: 1099px)").matches) return;
      var hero = document.querySelector(".hero");
      if (!hero) return;
      var rect = hero.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;
      parallaxEls.forEach(function (el) {
        var factor = parseFloat(el.getAttribute("data-parallax")) || 0;
        el.style.transform = "translateY(" + (rect.top * -factor) + "px)";
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---- Sign-up deadline countdown ----
  document.querySelectorAll("[data-deadline]").forEach(function (box) {
    var target = new Date(box.getAttribute("data-deadline"));
    if (isNaN(target.getTime())) return;
    var daysEl = box.querySelector("[data-deadline-days]");
    var hoursEl = box.querySelector("[data-deadline-hours]");
    var tick = function () {
      var diff = target.getTime() - Date.now();
      if (diff <= 0) {
        box.hidden = true;
        return;
      }
      box.hidden = false;
      var days = Math.floor(diff / 86400000);
      var hours = Math.floor((diff % 86400000) / 3600000);
      daysEl.textContent = String(days);
      hoursEl.textContent = String(hours);
    };
    tick();
    setInterval(tick, 60000);
  });

  // ---- Hike list filters (audience + two selects: difficulty/month on upcoming, country/year on past) ----
  var filterBar = document.getElementById("hikeFilters");
  var hikeGrid = document.getElementById("hikeGrid");
  if (filterBar && hikeGrid) {
    var audienceBtns = filterBar.querySelectorAll("[data-audience]");
    var selectA = document.getElementById("filterDifficulty") || document.getElementById("filterCountry");
    var attrA = document.getElementById("filterDifficulty") ? "data-difficulty" : "data-country";
    var selectB = document.getElementById("filterMonth") || document.getElementById("filterYear");
    var attrB = document.getElementById("filterMonth") ? "data-month" : "data-year";
    var countEl = document.getElementById("hikeCount");
    var lang = document.documentElement.lang;
    var isPast = hikeGrid.hasAttribute("data-past-list");
    var activeAudience = "all";
    var revealed = false;
    var showMoreBtn = document.getElementById("showMoreHikes");
    var pageSize = parseInt(hikeGrid.getAttribute("data-page-size"), 10) || Infinity;

    var applyFilters = function () {
      var a = selectA ? selectA.value : "";
      var b = selectB ? selectB.value : "";
      var visible = 0;
      var cards = hikeGrid.querySelectorAll("[data-audience]");
      var filtering = activeAudience !== "all" || a || b;
      cards.forEach(function (card) {
        var matches = (activeAudience === "all" || card.getAttribute("data-audience") === activeAudience) &&
          (!a || card.getAttribute(attrA) === a) &&
          (!b || card.getAttribute(attrB) === b);
        var withinPage = filtering || revealed || visible < pageSize;
        card.hidden = !matches || !withinPage;
        if (matches) visible++;
      });
      if (showMoreBtn) showMoreBtn.hidden = filtering || revealed || cards.length <= pageSize;
      if (countEl) {
        countEl.textContent = isPast
          ? (lang === "hu" ? "Eddig " + visible + " túra" : visible + " hike" + (visible === 1 ? "" : "s") + " so far")
          : (lang === "hu" ? visible + " túra időponttal" : visible + " hike" + (visible === 1 ? "" : "s") + " with dates");
      }
    };

    audienceBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        audienceBtns.forEach(function (o) {
          o.classList.remove("btn-primary");
          o.classList.add("btn-secondary");
          o.setAttribute("aria-pressed", "false");
        });
        b.classList.remove("btn-secondary");
        b.classList.add("btn-primary");
        b.setAttribute("aria-pressed", "true");
        activeAudience = b.getAttribute("data-audience");
        applyFilters();
      });
    });
    if (selectA) selectA.addEventListener("change", applyFilters);
    if (selectB) selectB.addEventListener("change", applyFilters);
    if (showMoreBtn) {
      showMoreBtn.addEventListener("click", function () {
        revealed = true;
        applyFilters();
      });
    }
    applyFilters();
  }

  // ---- Photo gallery -> lightbox ----
  var lightbox = document.getElementById("lightbox");
  if (lightbox) {
    var lbImage = document.getElementById("lbImage");
    var lbCounter = document.getElementById("lbCounter");
    var lbThumbs = document.getElementById("lbThumbs");
    var lbPrev = document.getElementById("lbPrev");
    var lbNext = document.getElementById("lbNext");
    var lbClose = document.getElementById("lbClose");
    var photos = [];
    var index = 0;

    var render = function () {
      lbImage.src = photos[index];
      lbCounter.textContent = (index + 1) + " / " + photos.length;
      lbThumbs.querySelectorAll("img").forEach(function (img, i) {
        img.classList.toggle("on", i === index);
      });
      lbPrev.hidden = lbNext.hidden = photos.length < 2;
    };

    var open = function (photoList, startIndex) {
      photos = photoList;
      index = startIndex || 0;
      lbThumbs.innerHTML = "";
      photos.forEach(function (src, i) {
        var img = document.createElement("img");
        img.src = src;
        img.alt = "";
        img.addEventListener("click", function () { index = i; render(); });
        lbThumbs.appendChild(img);
      });
      render();
      lightbox.hidden = false;
      document.body.classList.add("sheet-open");
      lbClose.focus();
    };

    var close = function () {
      lightbox.hidden = true;
      document.body.classList.remove("sheet-open");
    };

    document.querySelectorAll("[data-photos]").forEach(function (gallery) {
      var photoList = JSON.parse(gallery.getAttribute("data-photos"));
      gallery.querySelectorAll("[data-gallery-index]").forEach(function (item) {
        item.addEventListener("click", function () {
          open(photoList, parseInt(item.getAttribute("data-gallery-index"), 10) || 0);
        });
      });
    });
    document.querySelectorAll("[data-gallery-open]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var gallery = document.getElementById("hikeGallery");
        if (gallery) open(JSON.parse(gallery.getAttribute("data-photos")), 0);
      });
    });

    lbClose.addEventListener("click", close);
    lbPrev.addEventListener("click", function () { index = (index - 1 + photos.length) % photos.length; render(); });
    lbNext.addEventListener("click", function () { index = (index + 1) % photos.length; render(); });
    document.addEventListener("keydown", function (evt) {
      if (lightbox.hidden) return;
      if (evt.key === "Escape") close();
      if (evt.key === "ArrowLeft") { index = (index - 1 + photos.length) % photos.length; render(); }
      if (evt.key === "ArrowRight") { index = (index + 1) % photos.length; render(); }
    });
    var touchStartX = null;
    lightbox.addEventListener("touchstart", function (evt) { touchStartX = evt.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener("touchend", function (evt) {
      if (touchStartX === null) return;
      var dx = evt.changedTouches[0].clientX - touchStartX;
      if (Math.abs(dx) > 40) {
        index = dx > 0 ? (index - 1 + photos.length) % photos.length : (index + 1) % photos.length;
        render();
      }
      touchStartX = null;
    });
  }

  // ---- Booking bar visibility (phone only, upcoming hike pages) ----
  var bookBar = document.getElementById("bookBar");
  if (bookBar) {
    var toggleBookBar = function () {
      bookBar.classList.toggle("active", window.matchMedia("(max-width: 1099px)").matches);
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
