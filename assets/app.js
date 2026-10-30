(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.panel'));
  var nav = document.querySelector('.tabs');

  // 動きを減らす設定の人には、スムーススクロールもアニメーションも出さない。
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function activate(index) {
    tabs.forEach(function (tab, i) {
      var on = i === index;
      tab.classList.toggle('is-active', on);
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      // 選んでいるタブだけをタブ順に入れる（roving tabindex）。
      // 7つ全部がタブ停止だと、本文に入るまでに7回押すことになる。
      tab.tabIndex = on ? 0 : -1;
    });
    // 選んだタブを、タブ列の中で横に送って見えるようにする。
    //
    // scrollIntoView は使わない。block:'nearest' でも、タブ列が画面の下端に
    // かかっているとページごと縦に動く。読み込み直後に activate(0) を呼ぶので、
    // スマートフォンでトップページを開くと少し下から表示される原因になっていた。
    // 横方向だけを、タブ列の scrollLeft で動かす。
    var strip = tabs[index] && tabs[index].parentNode;
    if (strip && strip.scrollWidth > strip.clientWidth) {
      var t = tabs[index];
      strip.scrollLeft = t.offsetLeft - (strip.clientWidth - t.offsetWidth) / 2;
    }
    panels.forEach(function (panel, i) {
      var on = i === index;
      panel.hidden = !on;
      panel.classList.toggle('is-active', on);
    });
  }

  function scrollToY(y, smooth) {
    window.scrollTo({
      top: Math.max(y, 0),
      behavior: (smooth && !reduceMotion.matches) ? 'smooth' : 'instant'
    });
  }

  // ハッシュで指定された項目を含むタブを開いてから、その位置まで動かす。
  // 画像の遅延読み込みで上の要素の高さが変わると位置がずれるので、
  // 少しのあいだ位置を取り直して合わせ直す。
  function alignTo(target) {
    scrollToY(target.getBoundingClientRect().top + window.scrollY - nav.offsetHeight - 12, false);
  }

  function openByHash() {
    var id = decodeURIComponent(window.location.hash.replace('#', ''));
    // ハッシュが空（戻るで消えたとき）は、先頭のタブに戻す。
    // 何もしないと、タブは前のままでスクロールだけ飛んで迷子になる。
    if (!id) { activate(0); return false; }
    // 旧形式（#panel-0 など）で共有されたリンクを、いまの月齢のIDに読み替える。
    // 公開後に id を panel-N から m0/m4/… へ変えたので、古いリンクが切れないようにする。
    var pm = /^panel-(\d+)$/.exec(id);
    if (pm && panels[Number(pm[1])]) {
      id = panels[Number(pm[1])].id;
      history.replaceState(null, '', '#' + id);
    }
    // パネルそのものを指すハッシュ（#m0 など）は、そのタブを開いて先頭に合わせる。
    var pi = -1;
    for (var n = 0; n < panels.length; n++) { if (panels[n].id === id) { pi = n; break; } }
    if (pi >= 0) {
      activate(pi);
      scrollToY(panels[pi].getBoundingClientRect().top + window.scrollY - nav.offsetHeight, false);
      return true;
    }
    var target = document.getElementById(id);
    if (!target) return false;
    var panel = target.closest('.panel');
    if (!panel) return false;
    var index = panels.indexOf(panel);
    if (index < 0) return false;
    activate(index);

    window.requestAnimationFrame(function () { alignTo(target); });

    // 読み込みやレイアウトの確定で高さが変わったぶんを追従する。
    // 利用者が自分でスクロールを始めたら、そこで追従をやめる。
    var stop = false;
    function cancel() { stop = true; }
    window.addEventListener('wheel', cancel, { once: true, passive: true });
    window.addEventListener('touchstart', cancel, { once: true, passive: true });
    window.addEventListener('keydown', cancel, { once: true });

    [60, 180, 400, 800].forEach(function (ms) {
      window.setTimeout(function () { if (!stop) alignTo(target); }, ms);
    });
    // Google Fonts の確定までに十数秒かかることがあり、
    // 上の再調整（最大800ms）では間に合わず、約500pxずれていた。
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { if (!stop) alignTo(target); });
    }
    return true;
  }

  // タブを開く共通の処理。クリックでも矢印キーでも同じ動きにする。
  // 履歴に積むのは、積まないとURLが前の項目のまま画面だけ別タブになり、
  // そのURLを共有すると別の月齢の記事が開いてしまうため。
  function openTab(i) {
    activate(i);
    // 読み上げの位置を、開いたパネルの先頭へ移す。
    panels[i].focus({ preventScroll: true });
    scrollToY(panels[i].getBoundingClientRect().top + window.scrollY - nav.offsetHeight, true);
    var hash = '#' + panels[i].id;
    if (window.location.hash !== hash) history.pushState(null, '', hash);
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { openTab(i); });
    tab.addEventListener('keydown', function (e) {
      var next = null;
      if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      if (next === null) return;
      e.preventDefault();
      tabs[next].focus();
      openTab(next);
    });
  });

  // 用語の説明。マウスのない端末では軽くタップで開閉する。
  document.addEventListener('click', function (e) {
    var term = e.target.closest ? e.target.closest('.term') : null;
    document.querySelectorAll('.term.is-open').forEach(function (el) {
      if (el !== term) el.classList.remove('is-open');
    });
    if (term) {
      e.preventDefault();
      term.classList.toggle('is-open');
    }
  });

  // 用語の説明は Escape で閉じる。Enter と Space でも開閉できるようにする。
  // span なので、何もしないとキーボードからは開けない。
  document.addEventListener('keydown', function (e) {
    var el = document.activeElement;
    var onTerm = el && el.classList && el.classList.contains('term');
    if (e.key === 'Escape') {
      document.querySelectorAll('.term.is-open').forEach(function (t) {
        t.classList.remove('is-open');
      });
      if (onTerm) el.blur();
      return;
    }
    if (onTerm && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      el.classList.toggle('is-open');
    }
  });

  // ---------- 項目を横断して探す ----------
  // パネルは hidden なので、ブラウザのページ内検索では
  // 開いているタブの中しか見つからない。
  // 「ボタン電池」と覚えている人が、どのタブにあるかを
  // 当てなくても引けるようにする。
  //
  // 索引はHTMLに埋め込まず、最初に検索したときにDOMから作る。
  // 本文はすでにページの中にあるので、二重に持つ必要がない。
  // hidden なパネルの中身も textContent では読めるので、全文が対象になる。
  var input = document.getElementById('q');
  var results = document.getElementById('search-results');
  var index = null;

  function buildIndex() {
    return Array.prototype.map.call(document.querySelectorAll('.card'), function (card) {
      var panel = card.closest('.panel');
      var head = card.querySelector('.card-head h3');
      var sub = card.querySelector('.card-sub');
      return {
        id: card.id,
        i: panels.indexOf(panel),
        t: tabs[panels.indexOf(panel)].querySelector('.tab-label').textContent,
        n: head ? head.textContent.replace('#', '').trim() : card.id,
        s: sub ? sub.textContent.trim() : '',
        all: card.textContent
      };
    });
  }

  if (input && results) {
    function openItem(it) {
      activate(it.i);
      var target = document.getElementById(it.id);
      if (target) {
        alignTo(target);
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
        [60, 180, 400].forEach(function (ms) {
          window.setTimeout(function () { alignTo(target); }, ms);
        });
      }
      results.hidden = true;
      input.value = '';
    }

    function render(list) {
      results.innerHTML = '';
      if (!list.length) { results.hidden = true; return; }
      list.slice(0, 12).forEach(function (it) {
        var li = document.createElement('li');
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'search-hit';
        b.innerHTML = '<span class="search-tab"></span>'
                    + '<span class="search-name"></span>'
                    + '<span class="search-sub"></span>';
        b.querySelector('.search-tab').textContent = it.t;
        b.querySelector('.search-name').textContent = it.n;
        b.querySelector('.search-sub').textContent = it.s;
        b.addEventListener('click', function () { openItem(it); });
        li.appendChild(b);
        results.appendChild(li);
      });
      results.hidden = false;
    }

    function search(q) {
      q = q.trim();
      if (!q) { results.hidden = true; return; }
      if (!index) index = buildIndex();
      var hit = index.filter(function (it) { return it.all.indexOf(q) >= 0; });
      // 見出しとサブタイトルに入っているものを先に出す
      hit.sort(function (a, b) {
        var sa = (a.n.indexOf(q) >= 0 ? 2 : 0) + (a.s.indexOf(q) >= 0 ? 1 : 0);
        var sb = (b.n.indexOf(q) >= 0 ? 2 : 0) + (b.s.indexOf(q) >= 0 ? 1 : 0);
        return sb - sa;
      });
      render(hit);
    }

    input.addEventListener('input', function () { search(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { input.value = ''; results.hidden = true; }
      if (e.key === 'ArrowDown') {
        var first = results.querySelector('.search-hit');
        if (first) { e.preventDefault(); first.focus(); }
      }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest || !e.target.closest('.search')) results.hidden = true;
    });
  }

  // 目次へ戻る。0〜3か月タブは30項目で約130画面分あり、
  // 上端まで戻らないとタブに触れないのは、片手では現実的ではない。
  var toToc = document.getElementById('to-toc');
  if (toToc) {
    toToc.addEventListener('click', function () {
      var panel = panels.filter(function (p) { return !p.hidden; })[0];
      var toc = panel && panel.querySelector('.toc');
      if (toc) scrollToY(toc.getBoundingClientRect().top + window.scrollY - nav.offsetHeight, true);
      else scrollToY(0, true);
    });
    window.addEventListener('scroll', function () {
      toToc.classList.toggle('is-shown', window.scrollY > 2000);
    }, { passive: true });
  }

  window.addEventListener('popstate', openByHash);
  window.addEventListener('hashchange', openByHash);
  openByHash();
})();
