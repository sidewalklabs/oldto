import History from './history';
import {hashToStateObject, stateObjectToHash, transitionToStateObject} from './url-state';
import {mapPromise} from './viewer';

const APP_NAME = 'OldTO';

// This should go in the $(function()) block below.
// It's exposed to facilitate debugging.
const h = new History(function(hash, cb) {
  hashToStateObject(hash.substr(1), cb);
});

// Ping Google Analytics with the current URL (e.g. after history.pushState).
// See http://stackoverflow.com/a/4813223/388951
function trackAnalyticsPageView() {
  const url = location.pathname + location.search  + location.hash;
  ga('send', 'pageview', { 'page': url });
}

const LOG_HISTORY_EVENTS = false;

$(function() {
  // Relevant UI methods:
  // - transitionToStateObject(obj)
  //
  // State/URL manipulation:
  // - stateObjectToHash()
  // - hashToStateObject()
  //
  // State objects look like:
  // {photo_id:string, g:string}

  // Returns URL fragments like '/#g:123'.
  const fragment = function(state) {
    return '/#' + stateObjectToHash(state);
  };

  const title = function(state) {
    if ('photo_id' in state) {
      return `${APP_NAME} - Photo ${state.photo_id}`;
    } else if ('g' in state) {
      // TODO: include cross-streets in the title
      return `${APP_NAME} - Grid`;
    } else {
      return APP_NAME;
    }
  };

  $(window)
    .on('showGrid', function(e, pos) {
      const state = {g:pos};
      h.pushState(state, title(state), fragment(state));
      trackAnalyticsPageView();
    }).on('hideGrid', function() {
      const state = {initial: true};
      h.goBackUntil('initial', [state, title(state), fragment(state)]);
    }).on('openPreviewPanel', function() {
      // This is a transient state -- it should immediately be replaced.
      const state = {photo_id: true};
      h.pushState(state, title(state), fragment(state));
    }).on('showPhotoPreview', function(e, photo_id) {
      const g = $('#expanded').data('grid-key');
      const state = {photo_id:photo_id};
      if (g === 'pop') state.g = 'pop';
      h.replaceState(state, title(state), fragment(state));
      trackAnalyticsPageView();
    }).on('closePreviewPanel', function() {
      const g = $('#expanded').data('grid-key');
      const state = {g: g};
      h.goBackUntil('g', [state, title(state), fragment(state)]);
    });

  // Update the UI in response to hitting the back/forward button,
  // a hash fragment on initial page load or the user editing the URL.
  $(h).on('setStateInResponseToUser setStateInResponseToPageLoad',
  function(e, state) {
    // It's important that these methods only configure the UI.
    // They must not trigger events, or they could cause a loop!
    transitionToStateObject(state);
  });

  $(h).on('setStateInResponseToPageLoad', function() {
    trackAnalyticsPageView();  // hopefully this helps track social shares
  });

  if (LOG_HISTORY_EVENTS) {
    $(window)
      .on('showGrid', function(e, pos) {
        console.log('showGrid', pos);
      }).on('hideGrid', function() {
        console.log('hideGrid');
      }).on('showPhotoPreview', function(e, photo_id) {
        console.log('showPhotoPreview', photo_id);
      }).on('closePreviewPanel', function() {
        console.log('closePreviewPanel');
      }).on('openPreviewPanel', function() {
        console.log('openPreviewPanel');
      });
    $(h).on('setStateInResponseToUser', function(e, state) {
      console.log('setStateInResponseToUser', state);
    }).on('setStateInResponseToPageLoad', function(e, state) {
      console.log('setStateInResponseToPageLoad', state);
    });
  }

  // To load from a URL fragment, the map object must be ready.
  mapPromise.done(function() {
    h.initialize();
  });
});
