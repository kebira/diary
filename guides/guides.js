/* 케비라 실전 노트 — 장중 체크 저장 (localStorage) */
(function () {
  var slug = document.body.getAttribute('data-slug') || 'guide';
  var KEY = 'kebira-guides-' + slug + '-check';
  var box = document.querySelector('.checks');
  if (!box) return;
  var inputs = Array.prototype.slice.call(box.querySelectorAll('input[type=checkbox]'));
  var cnt = box.querySelector('.cnt');
  var top = box.querySelector('.chk-top');
  var bar = box.querySelector('.bar i');
  var reset = box.querySelector('.reset');

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return [];
      var v = JSON.parse(raw);
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function save() {
    var on = inputs.filter(function (i) { return i.checked; }).map(function (i) {
      return i.getAttribute('data-i');
    });
    try { localStorage.setItem(KEY, JSON.stringify(on)); } catch (e) {}
  }
  function paint() {
    var on = inputs.filter(function (i) { return i.checked; }).length;
    var total = inputs.length;
    if (cnt) cnt.textContent = on;
    if (bar) bar.style.width = (total ? (on / total) * 100 : 0) + '%';
    if (top) top.classList.toggle('ok', on >= Math.min(6, total));
  }

  var saved = load();
  inputs.forEach(function (i) {
    if (saved.indexOf(i.getAttribute('data-i')) >= 0) i.checked = true;
    i.addEventListener('change', function () { save(); paint(); });
  });
  if (reset) reset.addEventListener('click', function () {
    inputs.forEach(function (i) { i.checked = false; });
    save(); paint();
  });
  paint();
})();
