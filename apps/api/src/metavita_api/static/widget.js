/**
 * MetaVita embeddable chat widget.
 *
 * Usage:
 *   <script src="https://api.example.com/widget.js"
 *           data-deployment="DEPLOYMENT_ID"
 *           data-api-key="PUBLISHABLE_KEY"
 *           data-title="Ask us anything"
 *           data-accent="#5B5BD6"
 *           defer></script>
 *
 * Renders a floating launcher + chat panel that posts to /serve/{deployment}.
 * Self-contained: no dependencies, scoped styles, Shadow DOM isolation.
 */
(function () {
  "use strict";

  var script = document.currentScript;
  if (!script) return;
  var deployment = script.getAttribute("data-deployment");
  var apiKey = script.getAttribute("data-api-key") || "";
  var title = script.getAttribute("data-title") || "Ask MetaVita";
  var accent = script.getAttribute("data-accent") || "#5B5BD6";
  // Derive the API base from the script's own src (…/widget.js).
  var base = script.src.replace(/\/widget\.js.*$/, "");
  if (!deployment) {
    console.error("[metavita] widget missing data-deployment");
    return;
  }

  var host = document.createElement("div");
  host.setAttribute("data-metavita-widget", "");
  document.body.appendChild(host);
  var root = host.attachShadow({ mode: "open" });

  var style = document.createElement("style");
  style.textContent =
    ":host{all:initial}" +
    "*{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}" +
    ".launcher{position:fixed;bottom:20px;right:20px;width:56px;height:56px;border-radius:50%;" +
    "background:" + accent + ";color:#fff;border:none;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.25);" +
    "font-size:24px;display:flex;align-items:center;justify-content:center;z-index:2147483000}" +
    ".panel{position:fixed;bottom:88px;right:20px;width:360px;max-width:calc(100vw - 40px);height:520px;" +
    "max-height:calc(100vh - 120px);background:#fff;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.28);" +
    "display:none;flex-direction:column;overflow:hidden;z-index:2147483000}" +
    ".panel.open{display:flex}" +
    ".head{background:" + accent + ";color:#fff;padding:14px 16px;font-weight:600;font-size:15px;" +
    "display:flex;justify-content:space-between;align-items:center}" +
    ".close{background:none;border:none;color:#fff;cursor:pointer;font-size:18px;line-height:1}" +
    ".thread{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;background:#F7F7FB}" +
    ".msg{padding:9px 12px;border-radius:12px;font-size:14px;line-height:1.45;max-width:85%;white-space:pre-wrap}" +
    ".user{align-self:flex-end;background:" + accent + ";color:#fff}" +
    ".bot{align-self:flex-start;background:#fff;border:1px solid #E6E6EF;color:#1A1A2E}" +
    ".composer{display:flex;gap:8px;padding:12px;border-top:1px solid #E6E6EF;background:#fff}" +
    ".composer input{flex:1;padding:9px 12px;border:1px solid #D6D6E0;border-radius:10px;font-size:14px;outline:none}" +
    ".composer input:focus{border-color:" + accent + "}" +
    ".composer button{background:" + accent + ";color:#fff;border:none;border-radius:10px;padding:0 14px;cursor:pointer;font-size:14px}" +
    ".composer button:disabled{opacity:.5;cursor:default}" +
    ".cites{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}" +
    ".cite{font-size:11px;background:#EFEFFB;color:" + accent + ";border-radius:6px;padding:1px 6px}";
  root.appendChild(style);

  var launcher = document.createElement("button");
  launcher.className = "launcher";
  launcher.setAttribute("aria-label", "Open chat");
  launcher.textContent = "💬";
  root.appendChild(launcher);

  var panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML =
    '<div class="head"><span></span><button class="close" aria-label="Close">✕</button></div>' +
    '<div class="thread"></div>' +
    '<form class="composer"><input type="text" placeholder="Type a message…" autocomplete="off"/>' +
    '<button type="submit">Send</button></form>';
  root.appendChild(panel);
  panel.querySelector(".head span").textContent = title;

  var thread = panel.querySelector(".thread");
  var form = panel.querySelector(".composer");
  var input = panel.querySelector("input");
  var sendBtn = panel.querySelector('button[type="submit"]');

  function toggle(open) {
    panel.classList.toggle("open", open);
    if (open) input.focus();
  }
  launcher.addEventListener("click", function () {
    toggle(!panel.classList.contains("open"));
  });
  panel.querySelector(".close").addEventListener("click", function () {
    toggle(false);
  });

  function addMsg(role, text) {
    var el = document.createElement("div");
    el.className = "msg " + (role === "user" ? "user" : "bot");
    el.textContent = text;
    thread.appendChild(el);
    thread.scrollTop = thread.scrollHeight;
    return el;
  }

  function renderCitations(el, citations) {
    if (!citations || !citations.length) return;
    var wrap = document.createElement("div");
    wrap.className = "cites";
    citations.forEach(function (c) {
      var chip = document.createElement("span");
      chip.className = "cite";
      chip.textContent = "[" + c.marker + "]";
      chip.title = c.snippet || "";
      wrap.appendChild(chip);
    });
    el.appendChild(wrap);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    addMsg("user", q);
    sendBtn.disabled = true;
    var botEl = addMsg("bot", "…");
    fetch(base + "/serve/" + deployment, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + apiKey,
      },
      body: JSON.stringify({ question: q }),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        botEl.textContent = data.answer || "(no answer)";
        renderCitations(botEl, data.citations);
      })
      .catch(function (err) {
        botEl.textContent = "Sorry, something went wrong. (" + err.message + ")";
      })
      .finally(function () {
        sendBtn.disabled = false;
        thread.scrollTop = thread.scrollHeight;
      });
  });
})();
