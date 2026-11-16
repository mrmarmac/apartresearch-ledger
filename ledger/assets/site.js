/* Commitment Ledger. Small page behaviour. Every page works without it, except filtering on the browse page. */
(function () {
  'use strict';
  var root = document.documentElement;

  // Theme: follows the system unless the reader chooses.
  var tb = document.getElementById('theme');
  function dark() {
    var t = root.getAttribute('data-theme');
    return t ? t === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function label() { if (tb) tb.textContent = dark() ? 'Light' : 'Dark'; }
  if (tb) {
    label();
    tb.addEventListener('click', function () {
      var next = dark() ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('ledger-theme', next); } catch (e) {}
      label();
    });
  }

  // Copy buttons.
  [].forEach.call(document.querySelectorAll('[data-copy]'), function (b) {
    b.addEventListener('click', function () {
      var text = b.getAttribute('data-copy'), old = b.textContent;
      function done() { b.textContent = 'Copied'; setTimeout(function () { b.textContent = old; }, 1400); }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { window.prompt && done(); });
      }
    });
  });

  // Browse page: search, filters, sorting. State lives in the address so a view can be shared.
  var list = document.getElementById('rows');
  if (!list) return;
  var rows = [].slice.call(list.children);
  var keys = ['q', 'lab', 'current', 'event', 'topic', 'sort'];
  var tag = '';
  var chips = [].slice.call(document.querySelectorAll('#tags .chip'));
  function el(k) { return document.getElementById('f-' + k); }
  function apply() {
    var v = {};
    keys.forEach(function (k) { v[k] = el(k).value.trim().toLowerCase(); });
    var words = v.q.split(/\s+/).filter(Boolean), n = 0;
    rows.forEach(function (r) {
      var d = r.dataset;
      var ok = (!v.lab || d.lab === v.lab) && (!v.current || d.current === v.current) && (!v.topic || d.topic === v.topic) &&
        (!v.event || d.events.split(' ').indexOf(v.event) >= 0) && (!tag || d.tags.split(' ').indexOf(tag) >= 0) &&
        words.every(function (w) { return d.text.indexOf(w) >= 0; });
      r.hidden = !ok;
      if (ok) n++;
    });
    document.getElementById('count').innerHTML = '<b>' + n + '</b> of ' + rows.length + ' commitments';
    document.getElementById('empty').hidden = n > 0;
    chips.forEach(function (c) { c.setAttribute('aria-pressed', c.dataset.tag === tag ? 'true' : 'false'); });
    var active = keys.some(function (k) { return k !== 'sort' && v[k]; }) || !!tag;
    document.getElementById('reset').hidden = !active;
    var p = new URLSearchParams();
    keys.forEach(function (k) { if (v[k] && !(k === 'sort' && v[k] === 'serious')) p.set(k, el(k).value.trim()); });
    if (tag) p.set('tag', tag);
    var s = p.toString();
    try { history.replaceState(null, '', s ? '?' + s : location.pathname); } catch (e) {}
  }
  function sort() {
    var how = el('sort').value;
    var by = {
      serious: function (r) { return +r.dataset.o; },
      developer: function (r) { return +r.dataset.od; },
      recent: function (r) { return -(+r.dataset.last); },
      changes: function (r) { return -(+r.dataset.n); }
    }[how] || function (r) { return +r.dataset.o; };
    rows.sort(function (a, b) { return by(a) - by(b) || (+a.dataset.o) - (+b.dataset.o); });
    rows.forEach(function (r) { list.appendChild(r); });
  }
  var p = new URLSearchParams(location.search);
  keys.forEach(function (k) {
    var given = p.get(k) || (k === 'lab' ? p.get('developer') : null);
    if (given) el(k).value = given;
    el(k).addEventListener(k === 'q' ? 'input' : 'change', function () { if (k === 'sort') sort(); apply(); });
  });
  tag = p.get('tag') || '';
  if (tag) { var more = document.getElementById('tagbox'); if (more) more.open = true; }
  chips.forEach(function (c) { c.addEventListener('click', function () { tag = (tag === c.dataset.tag) ? '' : c.dataset.tag; apply(); }); });
  document.getElementById('reset').addEventListener('click', function () {
    keys.forEach(function (k) { if (k !== 'sort') el(k).value = ''; });
    tag = '';
    apply();
    el('q').focus();
  });
  if (el('sort').value !== 'serious') sort();
  apply();
})();
