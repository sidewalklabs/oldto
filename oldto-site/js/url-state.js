// The URL looks like one of these:
// /
// /#photo_id
// /#g:lat,lon
// /#photo_id,g:lat,lon

import {countPhotos, getPopularPhotoIds, latLonToMarker, parseLatLon, createMarker, selectMarker, map, hideExpanded, setViewClass, showExpanded} from './viewer';
import {loadInfoForLatLon} from './photo-info';

// Returns {photo_id:string, g:string}
export function getCurrentStateObject() {
  if (!$('#expanded').is(':visible')) {
    return {};
  }
  const g = $('#expanded').data('grid-key');
  const selectedId = $('#grid-container').expandableGrid('selectedId');

  return selectedId ? { photo_id: selectedId, g: g } : { g: g };
}

// Converts the string after '#' in a URL into a state object,
// {photo_id:string, g:string}
// This is asynchronous because it may need to fetch ID->lat/lon info.
export function hashToStateObject(hash, cb) {
  const m = hash.match(/(.*),g:(.*)/);
  if (m) {
    cb({photo_id: m[1], g: m[2]});
  } else if (hash.substr(0, 2) === 'g:') {
    cb({g: hash.substr(2)});
  } else if (hash.length > 0) {
    const photo_id = hash;
    findLatLonForPhoto(photo_id, function(g) {
      cb({photo_id: hash, g: g});
    });
  } else {
    cb({});
  }
}

export function stateObjectToHash(state) {
  if (state.photo_id) {
    if (state.g === 'pop') {
      return state.photo_id + ',g:pop';
    } else {
      return state.photo_id;
    }
  }

  if (state.g) {
    return 'g:' + state.g;
  }
  return '';
}

// Change whatever is currently displayed to reflect the state in obj.
// This change may happen asynchronously.
// This won't affect the URL hash.
export function transitionToStateObject(targetState) {
  const currentState = getCurrentStateObject();

  // This normalizes the state, i.e. adds a 'g' field to if it's implied.
  // (it also strips out extraneous fields)
  hashToStateObject(stateObjectToHash(targetState), function(state) {
    if (JSON.stringify(currentState) === JSON.stringify(state)) {
      return;  // nothing to do.
    }

    setViewClass(state.photo_id ? 'view-photo' : state.g ? 'view-grid' : 'view-map');

    // Reset to map view.
    if (JSON.stringify(state) === '{}') {
      hideExpanded();
    }

    // Show a different grid?
    if (currentState.g !== state.g) {
      const latLon = state.g;
      let count = countPhotos(lat_lons[latLon]);
      if (state.g === 'pop') {
        count = getPopularPhotoIds().length;
      } else {
        // Highlight the marker, creating it if necessary.
        let marker = latLonToMarker[latLon];
        const latLng = parseLatLon(latLon);
        if (!marker) {
          marker = createMarker(latLon, latLng);
        }
        if (marker) {
          selectMarker(marker, count);
          if (!map.getBounds().contains(latLng)) {
            map.panTo(latLng);
          }
        }
      }
      loadInfoForLatLon(latLon).done(function(photo_ids) {
        showExpanded(state.g, photo_ids, state.photo_id);
      });
      return;
    }

    if (currentState.photo_id && !state.photo_id) {
      // Hide the selected photo
      $('#grid-container').expandableGrid('deselect');
    } else {
      // Show a different photo
      $('#grid-container').expandableGrid('select', state.photo_id);
    }
  });
}


export function findLatLonForPhoto(photoId, cb) {
  $.ajax({
    dataType: "json",
    url: '/api/layer/oldtoronto/' + photoId,
    success: function(featureOrFeatureCollection) {
      const feature = featureOrFeatureCollection.features ?
        featureOrFeatureCollection.features[0] : featureOrFeatureCollection;
      const [lon, lat] = feature.geometry.coordinates;
      cb(lat.toFixed(6) + ',' + lon.toFixed(6))
    }
  });
}
