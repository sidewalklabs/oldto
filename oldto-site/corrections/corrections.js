import {fillDetailsPanel} from '../js/fill-details';

function getCookie(name) {
  const b = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return b ? b.pop() : '';
}

function getParameterByName(name) {
  const url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
      results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}

const numCompleted = Number(getParameterByName('num') || '0');
if (numCompleted === 1) {
  $('.popup').show();
}

const id = getParameterByName('id');
const dataPromise = $.get(`/api/layer/oldtoronto/${id}`);

const target = getParameterByName('target');
if (target) {
  $('form').attr('target', target);
}

function initMap() {
  let initLatLng;

  const geocoder = new google.maps.Geocoder();
  var map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 43.652505, lng: -79.384424},
    zoom: 13
  });
  window.map = map;  // for debugging
  var marker = null;
  var card = document.getElementById('pac-card');
  var input = document.getElementById('pac-input');

  function updateHiddenFieldWithLatLng(latLng) {
    if (latLng.equals(initLatLng)) {
      $('#submit').text('Location is correct');
      $('#reset').hide();
    } else {
      $('#submit').text('Submit correction');
      $('#reset').show();
    }

    $('#lat').val(latLng.lat());
    $('#lng').val(latLng.lng());
  }

  function setMarkerLatLng(latLng) {
    marker.setPosition(latLng);
    marker.setMap(map);
    updateHiddenFieldWithLatLng(latLng);
  }

  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(card);

  var autocomplete = new google.maps.places.Autocomplete(input);

  google.maps.event.addDomListener(input, 'keydown', function(event) {
    if (event.keyCode === 13) {
      event.preventDefault();
    }
  });

  // Bind the map's bounds (viewport) property to the autocomplete object,
  // so that the autocomplete requests use the current map bounds for the
  // bounds option in the request.
  autocomplete.bindTo('bounds', map);

  marker = new google.maps.Marker({
    map: null,  // Hidden initially
    position: map.getCenter(),
    draggable: true,
    animation: google.maps.Animation.DROP
  });

  google.maps.event.addListener(marker, 'dragend', function() {
    updateHiddenFieldWithLatLng(marker.getPosition());
    $('#method').val('drag');
    $('#last-search').val('');
  });

  map.addListener('click', function(e) {
    setMarkerLatLng(e.latLng);
    $('#method').val('map-click');
  });

  autocomplete.addListener('place_changed', function() {
    var place = autocomplete.getPlace();
    if (!place.geometry) {
      // User entered the name of a Place that was not suggested and
      // pressed the Enter key, or the Place Details request failed.
      geocoder.geocode({
        address: place.name,
        componentRestrictions: {
          country: 'CA',
          administrativeArea: 'ON',
          locality: 'Toronto'
        }
      }, function(results, status) {
        console.log(status, results);
        const geometry = results[0].geometry;
        if (geometry) {
          setMarkerLatLng(geometry.location);
          map.fitBounds(geometry.viewport);
          $('#method').val('search');
          $('#last-search').val(place.name);
        }
      });
      return;
    }

    // If the place has a geometry, then present it on a map.
    if (place.geometry.viewport) {
      map.fitBounds(place.geometry.viewport);
    } else {
      map.setCenter(place.geometry.location);
      map.setZoom(17);  // Why 17? Because it looks good.
    }
    setMarkerLatLng(place.geometry.location);
    $('#method').val('search');
    $('#last-search').val(place.name);
  });

  dataPromise.done(feature => {
    const [lng, lat] = feature.geometry.coordinates;
    const {properties} = feature;
    const {image} = properties;

    const $pane = $('.inputside');
    fillDetailsPanel(feature.id, properties, $pane);

    $pane.find('a img').attr('src', image.url);
    $('#photo-id').val(feature.id);

    $('#loading').hide();
    $('.container').show();

    const latLng = new google.maps.LatLng(lat, lng);
    initLatLng = latLng;
    $('#init-lat').val(lat);
    $('#init-lng').val(lng);
    setMarkerLatLng(latLng);
    map.setCenter(latLng);
    map.setZoom(15);
  });

  $('#reset').on('click', () => {
    setMarkerLatLng(initLatLng);
  });
}

$('button[type="submit"]').on('click', function() {
  $('#outcome').val($(this).text());  // record which button was clicked.
  $('#user-cookie').val(getCookie('_gid'));
  // do validation here.
});

$('form').on('submit', function() {
  const next = getParameterByName('next');  // 'random' is default; could be 'location'

  let newId;
  if (next === 'location') {
    // Pick the next image from this location.
    const idNum = Number(id);
    for (const ll in ll_to_ids) {
      const ids = ll_to_ids[ll];
      const idx = ids.indexOf(idNum);
      if (idx >= 0) {
        newId = ids[(idx + 1) % ids.length];
        break;
      }
    }
  } else {
    // Pick a random image from a random location.
    // This is deliberately _not_ a uniform sample of photos. We want location coverage.
    const locs = Object.keys(ll_to_ids);
    const loc = locs[Math.floor(Math.random() * locs.length)];
    const idsForLoc = ll_to_ids[loc];
    newId = idsForLoc[Math.floor(Math.random() * idsForLoc.length)];
  }
  const params = {
    id: newId,
    num: numCompleted + 1
  };
  if (next) {
    params.next = next;
  }
  if (target) {
    params.target = target;
  }

  // Wait 100ms to make sure the form submission goes through.
  window.setTimeout(function() {
    document.location.search = '?' + $.param(params);
  }, 100);
});

window.initMap = initMap;  // Move into the global scope for gmaps.
