(function () {
  var root = document.documentElement;
  root.classList.add("js");

  // theme: remembered per browser, falls back to system preference
  try { var saved = localStorage.getItem("theme"); if (saved) root.setAttribute("data-theme", saved); } catch (e) {}
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) toggle.addEventListener("click", function () {
    var cur = root.getAttribute("data-theme") ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  // nav border + brand once scrolled past hero
  var nav = document.querySelector(".topnav");
  var onScroll = function () { nav.classList.toggle("scrolled", window.scrollY > 120); };
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  // click a TOC graphic to enlarge it
  var lb = document.querySelector(".lightbox");
  if (lb && lb.showModal) {
    var lbImg = lb.querySelector("img");
    document.querySelectorAll("[data-zoom]").forEach(function (b) {
      b.addEventListener("click", function () {
        var img = b.querySelector("img");
        lbImg.src = b.getAttribute("data-zoom"); lbImg.alt = img ? img.alt : "";
        lb.showModal();
      });
    });
    lb.addEventListener("click", function () { lb.close(); });
  }

  if (!("IntersectionObserver" in window)) {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
    return;
  }


  // highlight current section in nav
  var links = {};
  document.querySelectorAll(".nav-links a").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      Object.values(links).forEach(function (a) { a.classList.remove("active"); });
      var a = links[e.target.id];
      if (a) {
        a.classList.add("active");
        // keep the active link visible in the (horizontally scrollable) nav WITHOUT touching page scroll
        var bar = a.parentNode, l = a.offsetLeft, r = l + a.offsetWidth;
        if (l < bar.scrollLeft || r > bar.scrollLeft + bar.clientWidth) bar.scrollLeft = l - 16;
      }
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  document.querySelectorAll("main section[id]").forEach(function (s) { spy.observe(s); });
})();
