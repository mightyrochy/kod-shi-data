"use strict";

window.MirrorMaterial = (() => {
  const preferenceKey = "liusterko-material";
  const changeEvent = "mirror-material-change";
  const labels = Object.freeze({
    kahlia: "Кахля",
    vytynanka: "Витинанка",
    klyny: "Клини"
  });
  const hex = /^#(?:[a-f\d]{3,4}|[a-f\d]{6}|[a-f\d]{8})$/i;

  function keyFor(value) {
    const id = value === "kahlja" ? "kahlia" : value;
    return typeof id === "string" && Object.hasOwn(labels, id) ? id : null;
  }

  function read(key, field) {
    try {
      const raw = window.localStorage.getItem(key);
      if (raw == null) return null;
      return keyFor(field ? JSON.parse(raw)?.[field] : raw);
    } catch {
      return null;
    }
  }

  function previousSelection() {
    return read(preferenceKey) ||
      read("liusterko-mirror-3", "hand") ||
      read("liusterko-studio-v2", "theme") ||
      read("liusterko-interface-v1", "theme") ||
      read("люстерко-тема") ||
      "vytynanka";
  }

  let active = previousSelection();
  document.documentElement.dataset.mirrorMaterial = active;

  function apply(id) {
    if (id === active) return;
    const previous = active;
    active = id;
    document.documentElement.dataset.mirrorMaterial = id;
    window.dispatchEvent(new CustomEvent(changeEvent, {detail: {theme: id, previous}}));
  }

  function set(value) {
    const id = keyFor(value);
    if (!id) return false;
    try { window.localStorage.setItem(preferenceKey, id); } catch {}
    apply(id);
    return true;
  }

  window.addEventListener("storage", event => {
    if (event.key !== preferenceKey && event.key !== null) return;
    apply(keyFor(event.newValue) || previousSelection());
  });

  function label(theme = active) { return labels[keyFor(theme)] || ""; }
  function get() { return active; }

  function mast() { return window.Hand.wordmark(active); }

  function petal(color, size = 18) {
    return window.Hand.petal(active, typeof color === "string" && hex.test(color) ? color : null, size);
  }

  // Selection is a paper slip, a pool of glaze or a tilted plane underneath the actual control.
  function choice(color, width = 92, height = 32) {
    const pigment = typeof color === "string" && hex.test(color) ? color : undefined;
    return window.Hand.patch(active, pigment, width, height);
  }

  // The host supplies its measured stage. No synthetic stage or timer runs here.
  function waiting(phase) {
    if (!Number.isInteger(phase) || phase < 1 || phase > 5) return "";
    return window.Hand.art(active, "waiting", phase);
  }

  function error() { return window.Hand.art(active, "error"); }

  function seal(colors, worn = false, size = 64) {
    const pigments = Array.isArray(colors) ? colors.filter(c => typeof c === "string" && hex.test(c)) : [];
    if (!pigments.length) return "";
    return window.Hand.seal(active, pigments, worn === true, size);
  }

  return Object.freeze({get, set, labels, label, mast, petal, choice, waiting, error, seal, changeEvent});
})();
