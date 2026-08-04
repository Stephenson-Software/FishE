// The FishE browser client: renders the screen JSON that every web front-end
// publishes, and hands the player's response back to whatever is driving it.
//
// Two front-ends share this file, so the game looks and behaves identically in
// both and a screen type only ever has to be implemented once:
//
//   - WebUserInterface (src/ui/webUserInterface.py) — the game runs on a
//     server; the page polls GET /state and POSTs to /input.
//   - PyodideUserInterface (src/ui/pyodideUserInterface.py) — the game runs in
//     this browser under Pyodide; screens arrive as Worker messages and input
//     goes back over a SharedArrayBuffer ring.
//
// A host wires itself up with FisheClient.init(sendFn) and then calls
// FisheClient.render(screen) for each screen the game publishes. The screen
// JSON contract is BaseUserInterface's primitives — see WebUserInterface.

window.FisheClient = (function () {
  let currentScreen = null;
  let sendToGame = () => {};

  function app() {
    return document.getElementById("app");
  }

  function el(tag, props, ...kids) {
    const e = document.createElement(tag);
    Object.assign(e, props || {});
    for (const k of kids) e.append(k);
    return e;
  }

  // The reason option i can't be picked, or null. Older screens (and any
  // front-end that never marks anything unavailable) simply omit the list.
  function unavailableReason(screen, i) {
    return (screen.unavailable || [])[i] || null;
  }

  function renderNotice(text, className) {
    const a = app();
    a.innerHTML = "";
    a.append(el("div", { className: className || "notice", textContent: text }));
  }

  function renderDisconnected() {
    currentScreen = null;
    renderNotice("Lost connection to the game — is it still running? Retrying…", "notice warning");
  }

  // Nothing is on screen between sending a response and the next screen
  // arriving, so drop currentScreen to make stray keypresses inert.
  function send(value) {
    currentScreen = null;
    app().innerHTML = "&hellip;";
    sendToGame(value);
  }

  function render(screen) {
    const a = app();
    a.innerHTML = "";
    currentScreen = screen;  // let keyboard shortcuts act on what's on screen
    if (!screen || screen.type === "loading") { renderNotice("Waiting for the game…"); return; }
    if (screen.type === "ended") { renderNotice("The game has ended. You can close this tab."); return; }
    if (screen.header) {
      const h = screen.header;
      const header = el("div", { className: "header" });
      // Each stat is its own chip; the flex-wrap row spaces them with whitespace
      // and wraps cleanly on narrow screens instead of running off one long line.
      const addPart = (content) => {
        header.append(content instanceof Node ? content : el("span", { textContent: content }));
      };
      addPart(`Day ${h.day}`);
      addPart(h.time);
      addPart(`$${h.money.toFixed(2)}`);
      addPart(`Fish: ${h.fish}`);
      // Below the fishing threshold (10) the player is too tired to fish — flag it.
      const energy = el("span", { textContent: `Energy: ${h.energy}/${h.maxEnergy}` });
      if (h.energy < 10) energy.className = "low";
      addPart(energy);
      if (h.location) addPart(h.location);
      if (h.goal) addPart(`Goal: ${h.goal}`);
      if (h.operator) addPart(el("span", { textContent: "OPERATOR MODE", className: "operator" }));
      a.append(header);
      document.title = `FishE — Day ${h.day}, $${h.money.toFixed(2)}`;
    }
    if (screen.descriptor) a.append(el("div", { className: "descriptor", textContent: screen.descriptor }));
    if (screen.prompt) a.append(el("div", { className: "prompt", textContent: screen.prompt }));
    if (screen.type === "options") {
      screen.options.forEach((opt, i) => {
        // An option the game would refuse right now is still listed, so the
        // menu doesn't shuffle under the player, but it is greyed out and
        // carries the reason - the button itself says why it can't be used.
        const reason = unavailableReason(screen, i);
        const b = el("button", {
          className: reason ? "unavailable" : (/delete/i.test(opt) ? "danger" : ""),
        });
        b.append(`[${i + 1}] ${opt}`);
        if (reason) {
          b.append(el("span", { className: "reason", textContent: ` — ${reason}` }));
          b.disabled = true;
          b.title = reason;
        } else {
          b.onclick = () => send(String(i + 1));
        }
        a.append(b);
      });
    } else if (screen.type === "dialogue") {
      a.append(el("div", { className: "dialogue", textContent: screen.text }));
      const b = el("button", { textContent: "Continue", className: "action" });
      b.onclick = () => send("");
      a.append(b);
    } else if (screen.type === "prompt") {
      a.append(el("div", { className: "descriptor", textContent: screen.text }));
      const inp = el("input", { type: "text" });
      const b = el("button", { textContent: "Submit", className: "action" });
      const valid = () => !screen.numeric ||
        (inp.value.trim() !== "" && !isNaN(Number(inp.value)));
      const submit = () => { if (valid()) send(inp.value); };
      if (screen.numeric) {
        inp.inputMode = "decimal";
        inp.placeholder = "Enter a number";
        inp.oninput = () => { b.disabled = !valid(); };
        b.disabled = true;  // nothing valid typed yet
      }
      inp.onkeydown = (e) => { if (e.key === "Enter") submit(); };
      b.onclick = submit;
      a.append(inp); a.append(b); inp.focus();
    } else if (screen.type === "busy") {
      // A pause the game takes on its own — shown, but with nothing to click;
      // the next screen replaces it when the pause is over.
      a.append(el("div", { className: "descriptor", textContent: screen.message }));
    } else if (screen.type === "timed") {
      a.append(el("div", { className: "descriptor", textContent: screen.message }));
      const b = el("button", { textContent: "React!", className: "action" });
      b.onclick = () => send("");
      a.append(b);
    }
  }

  // Keyboard control, matching the console/pygame front-ends: number keys pick
  // an option; Enter or Space advances a dialogue or the timed prompt. Typing
  // in the text field is left to the field itself.
  function onKeyDown(e) {
    const s = currentScreen;
    if (!s) return;
    if (e.target && e.target.tagName === "INPUT") return;
    if (s.type === "options") {
      if (e.key >= "1" && e.key <= "9") {
        const n = parseInt(e.key, 10);
        // A greyed-out option is no more pickable by its number key than by
        // its button; the game would ignore the response either way.
        if (n <= s.options.length && !unavailableReason(s, n - 1)) {
          e.preventDefault();
          send(String(n));
        }
      }
    } else if (s.type === "dialogue" || s.type === "timed") {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); send(""); }
    }
  }

  function init(sendFn) {
    sendToGame = sendFn;
    document.addEventListener("keydown", onKeyDown);
  }

  return {
    init: init,
    render: render,
    renderNotice: renderNotice,
    renderDisconnected: renderDisconnected,
    getCurrentScreen: () => currentScreen,
  };
})();
