/**
 * Yuho embeddable playground widget.
 *
 * Usage:
 *   <div id="yuho-editor"></div>
 *   <script src="widget.js"></script>
 *   <script>YuhoWidget.mount("yuho-editor", { apiUrl: "http://localhost:8080" })</script>
 */
(function (root) {
  "use strict";
  var YuhoWidget = {};
  YuhoWidget.mount = function (elementId, opts) {
    opts = opts || {};
    var apiUrl = (opts.apiUrl || "http://localhost:8080").replace(/\/$/, "");
    var el = document.getElementById(elementId);
    if (!el) throw new Error("Element not found: " + elementId);
    el.innerHTML =
      '<div style="display:flex;flex-direction:column;height:100%;font-family:monospace;background:#1e1e2e;color:#cdd6f4;border-radius:8px;overflow:hidden">' +
        '<div style="padding:8px 12px;background:#181825;font-size:13px;display:flex;justify-content:space-between;align-items:center">' +
          '<span>Yuho Playground</span>' +
          '<select id="yuho-w-target" style="background:#313244;color:#cdd6f4;border:none;padding:4px 8px;border-radius:4px">' +
            '<option value="json">JSON</option><option value="english">English</option><option value="latex">LaTeX</option>' +
            '<option value="mermaid">Mermaid</option><option value="prolog">Prolog</option>' +
          '</select>' +
        '</div>' +
        '<div style="display:flex;flex:1;min-height:0">' +
          '<textarea id="yuho-w-input" style="flex:1;background:#1e1e2e;color:#cdd6f4;border:none;padding:12px;resize:none;font-family:inherit;font-size:13px" placeholder="Enter Yuho source..."></textarea>' +
          '<pre id="yuho-w-output" style="flex:1;background:#181825;margin:0;padding:12px;overflow:auto;font-size:13px;border-left:1px solid #313244"></pre>' +
        '</div>' +
      '</div>';
    var input = document.getElementById("yuho-w-input");
    var output = document.getElementById("yuho-w-output");
    var targetSel = document.getElementById("yuho-w-target");
    var debounce = null;
    function run() {
      var source = input.value;
      if (!source.trim()) { output.textContent = ""; return; }
      var target = targetSel.value;
      fetch(apiUrl + "/v1/transpile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: source, target: target }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) output.textContent = data.data.output;
          else output.textContent = "Error: " + (data.error ? (data.error.message || JSON.stringify(data.error)) : "unknown");
        })
        .catch(function (e) { output.textContent = "Fetch error: " + e.message; });
    }
    input.addEventListener("input", function () {
      clearTimeout(debounce);
      debounce = setTimeout(run, 400);
    });
    targetSel.addEventListener("change", run);
  };
  root.YuhoWidget = YuhoWidget;
})(typeof window !== "undefined" ? window : this);
