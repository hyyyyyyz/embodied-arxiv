// Client-side topic filter for the daily card grid.
// Material's navigation.instant replaces the body on every page nav, so we
// rebind via Material's `document$` observable on every page load.

(function () {
  function init() {
    var filter = document.querySelector('.topic-filter');
    if (!filter) return;
    var buttons = filter.querySelectorAll('.topic-filter-btn');
    var grid = document.querySelector('.paper-grid');
    if (!grid) return;
    var cards = grid.querySelectorAll('.paper-card');

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var topic = btn.getAttribute('data-topic');

        buttons.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');

        cards.forEach(function (card) {
          var cardTopic = card.getAttribute('data-topic');
          if (topic === 'all' || cardTopic === topic) {
            card.classList.remove('hidden');
          } else {
            card.classList.add('hidden');
          }
        });
      });
    });
  }

  if (typeof document$ !== 'undefined' && document$.subscribe) {
    document$.subscribe(init);            // Material instant navigation
  } else if (document.readyState !== 'loading') {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
