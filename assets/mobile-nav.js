/* Native details provides Enter/Space activation and expanded state without JS. */
(() => {
  const menus = [...document.querySelectorAll('.mobile-menu')];
  function closeMenus() {
    menus.forEach(menu => { menu.open = false; });
  }
  menus.forEach(menu => {
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
    menu.addEventListener('click', event => {
      const link = event.target.closest('a');
      if (!link) return;
      menu.open = false;
      const href = link.getAttribute('href');
      const target = href.startsWith('#') && document.getElementById(href.slice(1));
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({preventScroll: true});
      } else {
        menu.querySelector('summary').focus();
      }
    });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.mobile-menu')) closeMenus();
  });
  document.querySelectorAll('[data-lang]').forEach(button => {
    button.addEventListener('click', () => {
      closeMenus();
      // The page's language handler has already switched the visible content.
      document.querySelector(`#${button.dataset.lang} [data-lang="${button.dataset.lang}"]`).focus({preventScroll: true});
      updateScopeLink();
    });
  });
  function updateScopeLink() {
    const link = document.querySelector('body > .topbar a[href^="#status"]');
    if (link) link.setAttribute('href', document.documentElement.lang === 'ja' ? '#status-ja' : '#status');
  }
  updateScopeLink();
  window.matchMedia('(max-width:560px)').addEventListener('change', closeMenus);
})();
