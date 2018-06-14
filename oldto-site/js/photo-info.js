import * as _ from 'underscore';

// This file manages all the photo information.
// Some of this comes in via lat-lons.js.
// Some is requested via XHR.

// Maps photo_id -> { title: ..., date: ..., library_url: ... }
const photoIdToInfo = {};

const latLonToName = {};

const SITE = '';
const BY_LOCATION_API = '/api/oldtoronto/by_location';

// e.g. "tpl", "cta" or undefined.
const source = (() => {
  const m = window.location.search.match(/source=([a-zA-Z]+)/);
  if (m) {
    return m[1];
  }
})();

// The callback is called with the photo_ids that were just loaded, after the
// UI updates.  The callback may assume that infoForPhotoId() will return data
// for all the newly-available photo_ids.
export function loadInfoForLatLon(latLonStr) {
  let url;
  if (latLonStr === 'pop') {
    url = SITE + '/popular.json';
  } else {
    const [lat, lon] = latLonStr.split(',');
    url = `${BY_LOCATION_API}?lat=${lat}&lng=${lon}`;
  }
  if (source) {
    url += `&source=${source}`;
  }

  return $.getJSON(url).then(function(responseData) {
    // Add these values to the cache.
    $.extend(photoIdToInfo, responseData);
    let photoIds = [];
    for (let k in responseData) {
      photoIds.push(k);
    }
    // Some browsers scramble the order of responses, so we need to sort.
    photoIds = _.sortBy(photoIds, id => photoIdToInfo[id].date);
    if (latLonStr !== 'pop') {
      latLonToName[latLonStr] = extractName(responseData);
    }
    return photoIds;
  });
}

// Returns a {title: ..., date: ..., library_url: ...} object.
// If there's no information about the photo yet, then the values are all set
// to the empty string.
export function infoForPhotoId(photoId) {
  return photoIdToInfo[photoId] ||
      { title: '', date: '', library_url: '' };
}

// Would it make more sense to incorporate these into infoForPhotoId?
export function descriptionForPhotoId(photoId) {
  const info = infoForPhotoId(photoId);
  let desc = info.title;
  if (desc) desc += ' ';
  const date = info.date.replace(/n\.d\.?/, 'No Date') || 'No Date';
  desc += date;
  return desc;
}

export function libraryUrlForPhotoId(photoId) {
  const info = infoForPhotoId(photoId);
  return info['url'];
}

function extractName(latLonJson) {
  // if any entries have an original_title, it's got to be a pure location.
  for (let k in latLonJson) {
    const v = latLonJson[k];
    if (v.original_title) return v.original_title;
  }
}
