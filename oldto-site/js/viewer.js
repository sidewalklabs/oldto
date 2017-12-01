import {libraryUrlForPhotoId, infoForPhotoId, loadInfoForLatLon} from './photo-info';
import {MAP_STYLE} from './map-styles';
import {popular_photos} from './popular-photos';
import {Popup} from './popup';
import {hideLocationMarker, locationMarker} from './search';

import * as _ from 'underscore';
import Clipboard from 'clipboard';

// URL base for social media sharing.
// The Facebook share button requires this; "localhost" URLs won't work in development.
const URL_FOR_SOCIAL = 'https://oldtoronto.sidewalklabs.com/';

const markers = [];
export const markerIcons = {
  images: null,  // these are filled in by initializeMap()
  filtered: null,
  selected: null,
  searchPin: null
};
export const latLonToMarker = {};
let selectedMarker, selectedIcon;

const MIN_YEAR = 1850;
const MAX_YEAR = 2018;
let yearRange = [MIN_YEAR, MAX_YEAR];

export let map;
export const mapPromise = $.Deferred();

let popup;  // initialized in initializeMap()

function isFullTimeRange(yearRange) {
  return (yearRange[0] === MIN_YEAR && yearRange[1] === MAX_YEAR);
}

// A photo is in the date range if any dates mentioned in it are in the range.
// For example, "1927; 1933; 1940" is in the range [1920, 1930].
function isPhotoInDateRange(info, yearRange) {
  if (isFullTimeRange(yearRange)) return true;

  const [first, last] = yearRange;
  const {date} = info;
  return (date && date >= first && date <= last);
}

export function countPhotos(yearToCounts) {
  if (isFullTimeRange(yearRange)) {
    // This includes undated photos.
    return _.reduce(yearToCounts, (a, b) => a + b);
  } else {
    const [first, last] = yearRange;
    return _.reduce(
        _.filter(yearToCounts, (c, y) => (y > first && y <= last)),
        (a, b) => a + b);
  }
}

// Make the given marker the currently selected marker.
// This is purely UI code, it doesn't touch anything other than the marker.
export function selectMarker(marker) {
  let zIndex = 0;
  if (selectedMarker) {
    zIndex = selectedMarker.getZIndex();
    selectedMarker.setIcon(selectedIcon);
  }

  if (marker) {
    selectedMarker = marker;
    selectedIcon = marker.getIcon();
    marker.setIcon(markerIcons.selected);
    marker.setZIndex(100000 + zIndex);
  }
}

// Update the date histogram and year labels for the time slider.
function updateYearLabels(opt_yearRange) {
  const [firstYear, lastYear] = opt_yearRange || yearRange;
  const width = $('.time-chart-bg').width();
  const leftPx = Math.floor((firstYear - MIN_YEAR) / (MAX_YEAR - MIN_YEAR) * width);
  const rightPx = Math.ceil((lastYear - MIN_YEAR) / (MAX_YEAR - MIN_YEAR) * width);
  const $fg = $('.time-chart-fg');
  $fg.css({
    'background-position-x': `-${leftPx}px`,
    'margin-left': `${leftPx}px`,
    'width': (rightPx - leftPx) + 'px'
  })

  $('#time-range-label-first').text(firstYear).css({left: `${leftPx}px`});
  $('#time-range-label-last').text(lastYear).css({left: `${rightPx}px`});
}

export function updateYears(firstYear, lastYear) {
  yearRange = [firstYear, lastYear];
  updateYearLabels();

  _.forEach(latLonToMarker, (marker, lat_lon) => {
    const count = countPhotos(lat_lons[lat_lon], yearRange);
    if (count) {
      marker.setIcon(markerIcons.images);
      marker.setZIndex(1);
    } else {
      marker.setIcon(markerIcons.filtered);
      marker.setZIndex(0);
    }
  });
  addNewlyVisibleMarkers();
  updateClearFilters();
}

// The callback gets fired when the info for all lat/lons at this location
// become available (i.e. after the /info RPC returns).
function displayInfoForLatLon(latLon, opt_selectCallback, opt_selectedId) {
  loadInfoForLatLon(latLon).done(function(photoIds) {
    let selectedId = opt_selectedId;

    if (!selectedId && photoIds.length <= 10) {
      selectedId = photoIds[0];
    }
    if (isMobileView() && photoIds.length > 1) {
      selectedId = null;
    }
    showExpanded(latLon, photoIds, selectedId);
    if (opt_selectCallback && selectedId) {
      opt_selectCallback(selectedId);
    }
  }).fail(function() {
  });
}

function handleClick(e, opt_latLon) {
  const latLon = opt_latLon || e.latLng.lat().toFixed(6) + ',' + e.latLng.lng().toFixed(6);
  const marker = latLonToMarker[latLon];
  selectMarker(marker, lat_lons[latLon]);

  loadInfoForLatLon(latLon).done(photoIds => {
    const numPhotos = countPhotos(lat_lons[latLon], yearRange);
    let photoId;
    const [first, last] = yearRange;

    if (isFullTimeRange(yearRange)) {
      photoId = photoIds[0];
    } else if (numPhotos) {
      // If the year filter is active, try to find a sample photo in the selected range.
      for (const id of photoIds) {
        const info = infoForPhotoId(id);
        if (isPhotoInDateRange(info, yearRange)) {
          photoId = id;
          break;
        }
      }
    }

    if (photoId) {
      const info = infoForPhotoId(photoId);
      const {width, height, thumb_url, title} = info;
      const thumbWidth = Math.floor(width / 5);
      const thumbHeight = Math.floor(height / 5);

      popup.contentDiv.innerHTML = `
      <div style="cursor: pointer" class="popup" onclick="" data-latlon="${latLon}" data-photoid="${photoId}">
        ${numPhotos > 1 ? `<div class="photo-count">+${numPhotos - 1}</div>` : ''}
        <img src="${thumb_url}" width="${thumbWidth}" height="${thumbHeight}">
        <div class="title">${title}</div>
      </div>
      `;
    } else {
      popup.contentDiv.innerHTML = `
      <div class="popup no-images">
        No photos between ${first} and ${last}.
        <a href="#" data-latlon="${latLon}" id="popup-showall">Show all.</a>
      </div>
      `;
    }
    popup.setMap(map);
    popup.position = marker.position;
    popup.draw();
    popup.photoIds = photoIds;
  });
}

export function initializeMap() {
  const center = new google.maps.LatLng(43.6486135, -79.3738487);
  const opts = {
    zoom: 15,
    maxZoom: 18,
    minZoom: 10,
    center: center,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    mapTypeControl: false,
    fullscreenControl: false,
    streetViewControl: true,
    panControl: false,
    styles: MAP_STYLE
  };

  map = new google.maps.Map($('#map').get(0), opts);
  window.map = map;  // for debugging / setting views programmatically

  // The OldSF UI just gets in the way of Street View.
  // Even worse, it blocks the "exit" button!
  const streetView = map.getStreetView();
  google.maps.event.addListener(streetView, 'visible_changed',
      function() {
        $('.streetview-hide').toggle(!streetView.getVisible());
      });

  // Create marker icons for each number.
  const makeMarker = (url, width, height) => ({
    url,
    size: new google.maps.Size(width, height),
    origin: new google.maps.Point(0, 0),
    anchor: new google.maps.Point((width + 2) / 4, (height + 2) / 4),
    scaledSize: new google.maps.Size(width / 2, height / 2)
  });
  markerIcons.images = makeMarker('images/knob-blue.png', 34, 34);
  markerIcons.selected = makeMarker('images/knob-black.png', 34, 34);
  markerIcons.filtered = makeMarker('images/knob-grey.png', 26, 26);
  markerIcons.searchPin = makeMarker('images/pin-black.png', 50, 72);
  markerIcons.searchPin.anchor.y = 35;  // bottom

  popup = new Popup(center, document.createElement('div'));

  // Adding markers is expensive -- it's important to defer this when possible.
  const idleListener = google.maps.event.addListener(map, 'idle', function() {
    google.maps.event.removeListener(idleListener);
    addNewlyVisibleMarkers();
    mapPromise.resolve(map);
  });

  google.maps.event.addListener(map, 'bounds_changed', function() {
    addNewlyVisibleMarkers();
  });

  google.maps.event.addListener(map, 'click', function() {
    // A click on the map background should hide any popups.
    popup.setMap(null);
    selectMarker(null);
  });
}

function addNewlyVisibleMarkers() {
  const bounds = map.getBounds();

  for (let latLon in lat_lons) {
    if (latLon in latLonToMarker) continue;

    const pos = parseLatLon(latLon);
    if (!bounds.contains(pos)) continue;

    createMarker(latLon, pos);
  }
}

/** Convert a "lat,lon" string to a google.maps.LatLng. */
export function parseLatLon(latLonStr) {
  const [lat, lon] = latLonStr.split(",");
  return new google.maps.LatLng(parseFloat(lat), parseFloat(lon));
}

/**
 * latLonStr is a "(lat),(lon)" string. latLng is a google.maps.LatLng object.
 */
export function createMarker(latLonStr, latLng) {
  const count = countPhotos(lat_lons[latLonStr], yearRange);
  const marker = new google.maps.Marker({
    position: latLng,
    map: map,
    flat: true,
    visible: true,
    icon: count ? markerIcons.images : markerIcons.filtered,
    title: latLonStr,
    zIndex: count ? 1 : 0
  });
  markers.push(marker);
  latLonToMarker[latLonStr] = marker;
  google.maps.event.addListener(marker, 'click', handleClick);
  return marker;
}


// NOTE: This can only be called when the info for all photo_ids at the current
// position have been loaded (in particular the image widths).
// key is used to construct URL fragments.
export function showExpanded(key, photoIds, opt_selectedId) {
  setViewClass('view-grid');
  map.set('keyboardShortcuts', false);
  $('#expanded').show().data('grid-key', key);
  if (isFullTimeRange(yearRange)) {
    $('#filtered-slideshow').hide();
  } else {
    const [first, last] = yearRange;
    $('#filtered-slideshow').show();
    $('#slideshow-filter-first').text(first);
    $('#slideshow-filter-last').text(last);
  }
  let images = $.map(photoIds, function(photoId) {
    const info = infoForPhotoId(photoId);
    if (!isPhotoInDateRange(info, yearRange)) return null;
    return $.extend({
      id: photoId,
      largesrc: info.image_url,
      src: info.thumb_url,
      width: 600,   // these are fallbacks
      height: 400
    }, info);
  });
  images = images.filter(image => image !== null);
  $('#grid-container').expandableGrid({
    rowHeight: 120,
    speed: 200 /* ms for transitions */
  }, images);
  if (opt_selectedId) {
    $('#grid-container').expandableGrid('select', opt_selectedId);
  }
  $(document).on('keyup', e => {
    // If the user hits escape while looking at a grid, close it.
    if (e.keyCode === 27 && $('.og-details').length === 0) {
      hideExpanded();
    }
  });
}

export function hideExpanded() {
  $('#expanded').hide();
  $(document).unbind('keyup');
  map.set('keyboardShortcuts', true);
  setViewClass('view-map');
}

function isMobileView() {
  return !$('.left-nav').is(':visible');
}

// This fills out details for either a thumbnail or the expanded image pane.
function fillPhotoPane(photoId, $pane) {
  // $pane is div.og-details

  const info = infoForPhotoId(photoId);
  const {archives_fields, geocode, url} = info;

  $pane.find('a.link').attr('href', url);
  $pane.find('a.feedback-button').attr('href', `/corrections/?id=${photoId}`);

  _.forEach(archives_fields, (v, k) => {
    if (v) {
      $pane.find(`.${k}`).show();
      $pane.find(`.value.${k}, a.${k}`).text(v || '');
    } else {
      $pane.find(`.${k}`).hide();  // hide both key & value if value is missing.
    }
  });
  $pane.find('.title').text(info.title);
  $pane.find('.geocode-debug').text(JSON.stringify(geocode, null, 2));
  $pane.find('.inline-image').attr({
    src: info.image_url
  }).css({
    height: Math.ceil(info.height / info.width * window.innerWidth) + 'px'
  });

  const canonicalUrl = `${URL_FOR_SOCIAL}/#${photoId}`;
  setViewClass('view-photo');

  // Social media links.
  // Some browser plugins block Twitter and Facebook, so we have to add these conditionally.
  $pane.find('.copy-link').attr('data-clipboard-text', canonicalUrl);

  if (typeof(twttr) !== 'undefined') {
    twttr.widgets.createShareButton(
      canonicalUrl,
      $pane.find('.tweet').get(0), {
        count: 'none',
        text: `${info.title} - ${info.date} #OldToronto @TorontoArchives`
      });
  }

  if (typeof(FB) !== 'undefined') {
    var $fb_holder = $pane.find('.facebook-holder');
    $fb_holder.empty().append($('<fb:like>').attr({
      'href': URL_FOR_SOCIAL,
      'hash': `#${photoId}`,
      'layout': 'button',
      'action': 'like',
      'show_faces': 'false',
      'share': 'true'
    }));
    FB.XFBML.parse($fb_holder.get(0));
  }

  // Scrolling the panel shouldn't scroll the whole grid.
  // See http://stackoverflow.com/a/10514680/388951
  // TODO(danvk): Consolidate with $.fn.scrollGuard.
  $pane.off("mousewheel").on("mousewheel", function(event) {
    const height = $pane.height();
    const scrollHeight = $pane.get(0).scrollHeight;
    const blockScrolling = (this.scrollTop === scrollHeight - height &&
                         event.deltaY < 0 || this.scrollTop === 0 &&
                         event.deltaY > 0);
    return !blockScrolling;
  });
}

function photoIdFromATag(a) {
  return $(a).attr('href').replace('/#', '');
}

export function getPopularPhotoIds() {
  return $('.popular-photo:visible a').map(function(_, a) {
    return photoIdFromATag(a);
  }).toArray();
}

export function fillPopularImagesPanel() {
  // Rotate the images daily.
  const elapsedMs = new Date().getTime() - new Date('2015/12/15').getTime();
  const elapsedDays = Math.floor(elapsedMs / 86400 / 1000);
  const shift = elapsedDays % popular_photos.length;
  const shownPhotos = popular_photos.slice(shift).concat(popular_photos.slice(0, shift));

  const makePanel = function(row) {
    const $panel = $('#popular-photo-template').clone().removeAttr('id');
    $panel.find('a').attr('href', '#' + row.id);
    $panel.find('img')
        .attr('border', '0')  // For IE8
        .attr('data-src', row.thumbnail_url)
        .attr('height', row.height);
    $panel.find('.desc').text(row.title);
    $panel.find('.loc').text(row.subtitle);
    if (row.date) $panel.find('.date').text(' (' + row.date + ')');
    return $panel.get(0);
  };

  const popularPhotos = $.map(shownPhotos, makePanel);
  $('#popular').append($(popularPhotos).show());
  $(popularPhotos).appear({force_process:true});
  $('#popular').on('appear', '.popular-photo', function() {
    const $img = $(this).find('img[data-src]');
    loadDeferredImage($img.get(0));
  });
}

function loadDeferredImage(img) {
  const $img = $(img);
  if ($img.attr('src')) return;
  $(img)
    .attr('src', $(img).attr('data-src'))
    .removeAttr('data-src');
}

// See http://stackoverflow.com/a/30112044/388951
$.fn.scrollGuard = function() {
  return this.on('mousewheel', function() {
    const scrollHeight = this.scrollHeight;
    const height = $(this).height();
    const blockScrolling = this.scrollTop === scrollHeight - height && event.deltaY < 0 || this.scrollTop === 0 && event.deltaY > 0;
    return !blockScrolling;
  });
};

/** Display or hide the "Clear Filters" link depending on the UI state. */
export function updateClearFilters() {
  const show = (!!locationMarker || !isFullTimeRange(yearRange));
  $('#clear-filters').toggle(show);
}

/**
 * Add a CSS class to the body to track which view we're in.
 * This is helpful for doing some dramatic rearranging via media queries on mobile.
 * view is one of 'view-map', 'view-grid' or 'view-photo'.
 */
export function setViewClass(view) {
  const allViews = 'view-grid view-map view-photo';
  $('body').removeClass(allViews).addClass(view);
}

$(function() {
  // Clicks on the background or "exit" button should leave the slideshow.
  const hide = () => {
    hideExpanded();
    $(window).trigger('hideGrid');
  };

  // A click anywhere on the "exit" link closes the expanded view.
  $(document).on('click', '#expanded .exit', hide);

  // This should be a click on the area outside the expanded panel.
  // (i.e. on the map itself.)
  $(document).on('click', '#expanded', function(e) {
    if (e.target === this) {
      hide();
    }
  });

  // Fill in the expanded preview pane.
  $('#grid-container').on('og-fill', 'li', function(e, div) {
    const id = $(this).data('image-id');
    $(div).empty().append(
        $('#image-details-template').clone().removeAttr('id').show());
    $(div).parent().find('.og-details-left').empty().append(
        $('#image-details-left-template').clone().removeAttr('id').show());
    fillPhotoPane(id, $(div));
  })
  .on('click', '.og-fullimg > img', () => {
    // The image should only be a link to the Archives on desktop/tablet.
    const isFullScreen = $('.og-expander-inner').css('position') === 'fixed';
    const photoId = $('#grid-container').expandableGrid('selectedId');
    if (!isFullScreen) {
      window.open(libraryUrlForPhotoId(photoId), '_blank');
    } else {
      const imageUrl = infoForPhotoId(photoId).image_url;
      if (imageUrl) {
        window.open(imageUrl, '_blank');
      }
    }
  })
  .on('og-deselect', () => {
    setViewClass('view-grid');
  })

  $(document).on('keyup', 'input, textarea', function(e) { e.stopPropagation(); });

  $('.popular-photo').on('click', 'a', function(e) {
    e.preventDefault();
    const selectedPhotoId = photoIdFromATag(this);

    loadInfoForLatLon('pop').done(function(photoIds) {
      showExpanded('pop', photoIds, selectedPhotoId);
      $(window).trigger('showGrid', 'pop');
      $(window).trigger('openPreviewPanel');
      $(window).trigger('showPhotoPreview', selectedPhotoId);
    }).fail(function() {
    });
  });

  // ... it's annoying that we have to do this. jquery.appear.js should work!
  $('#popular').on('scroll', function() {
    $(this).appear({force_process: true});
  });

  $('#grid-container').on('submit', 'form', function() {
    const $button = $(this).find('input[type="submit"]');
    $button.val('Thanks!').prop('disabled', true);  // prevent double-submits
  });

  $('#grid-container').on('og-select', 'li', function() {
    const photoId = $(this).data('image-id')
    $(window).trigger('showPhotoPreview', photoId);
  }).on('og-deselect', function() {
    $(window).trigger('closePreviewPanel');
  }).on('og-openpreview', function() {
    $(window).trigger('openPreviewPanel');
  });

  // Copy link button
  const clipboard = new Clipboard('.copy-link');
  clipboard.on('success', event => {
    // Keep the button a fixed width to reduce visual jumpiness.
    const $btn = $(event.trigger);
    const width = $btn.get(0).offsetWidth;
    $btn.css({width: `${width}px`}).addClass('clicked');
    $btn.find('.email-share').text('Copied!');
  });

  const updateDebounced = _.debounce(ui => {
    const [a, b] = ui.values;
    updateYears(a, b);
  }, 200);
  $('#time-slider').slider({
    range: true,
    min: MIN_YEAR,
    max: MAX_YEAR,
    values: yearRange,
    slide: (event, ui) => {
      const [a, b] = ui.values;
      updateYearLabels([a, b]);
      updateDebounced(ui);
    },
    stop: (event, ui) => {
      const [a, b] = ui.values;
      ga('send', 'event', 'link', 'time-slider', {
        'page': `/#${a}–${b}`
      });
    }
  });
  updateYearLabels();

  $('#clear-filters').on('click', () => {
    hideLocationMarker();
    updateYears(MIN_YEAR, MAX_YEAR);
    $('#time-slider').slider({
      values: yearRange
    });
    updateClearFilters();
  });

  $('#slideshow-all').on('click', () => {
    updateYears(MIN_YEAR, MAX_YEAR);
    $('#time-slider').slider({
      values: yearRange
    });
    const latLonStr = $('#expanded').data('grid-key');
    ga('send', 'event', 'link', 'time-slider-clear');
    hideExpanded();
    displayInfoForLatLon(latLonStr);
  });

  document.addEventListener('click', function(e) {
    const $link = $(e.target);
    if (!$link.is('#popup-showall')) return;

    e.stopPropagation();  // prevent the click from propagating through to the map.
    const latLonStr = $link.attr('data-latlon');

    updateYears(MIN_YEAR, MAX_YEAR);
    $('#time-slider').slider({
      values: yearRange
    });
    handleClick(null, latLonStr);
  }, true /* capture phase */);

  // Show the grid when the user clicks on a photo in a popup
  // We use capture phase here to get access to the event before Google Maps does.
  const popupOnClick = function(e) {
    const $popup = $(e.target).parents('.popup');
    if ($popup.length === 0) return;

    e.stopPropagation();  // prevent the click from propagating through to the map.
    const latLonStr = $popup.attr('data-latlon');
    const photoId = null; // $popup.attr('data-photoid');
    // if (!latLonStr || !photoId) return; // Maybe on a "no images" popup.
    if (!latLonStr) return;

    displayInfoForLatLon(latLonStr, function(photo_id) {
      $(window).trigger('openPreviewPanel');
      $(window).trigger('showPhotoPreview', photo_id);
    }, photoId);
    $(window).trigger('showGrid', latLonStr);
  };
  document.addEventListener('click', popupOnClick, true /* capture phase */);
  document.addEventListener('touchend', popupOnClick, true /* capture phase */);

  $(document).on('click', '.inline-close', () => {
    $('#grid-container').find('.og-close').trigger('click');
  });

  $(window).on('resize', () => {
    // In mobile view, we need to resize an expanded image to maintain its aspect ratio.
    if (!isMobileView()) return;
    const $pane = $('#expanded div.og-details');
    if ($pane.length === 0) return;
    const $img = $pane.find('.inline-image');
    if ($img.length === 0) return;
    const img = $img.get(0);
    $img.css({
      height: Math.ceil(img.naturalHeight / img.naturalWidth * window.innerWidth) + 'px'
    });
  });
});
