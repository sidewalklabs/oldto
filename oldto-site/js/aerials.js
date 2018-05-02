/* global mapboxgl */

const BASE_STYLE = 'mapbox://styles/rvilim/cjg87z8j1068k2sp653i9xpbm?fresh=true';

// TODO(danvk): show minor roads depending on zoom level, building names.
const LABEL_LAYERS = [
  'road_major',
  'road_major_label',
  'poi_label',
  'bridge_major',
  'bridge_minor'
]
const YEARS = [1947, 1983, 1985, 1987, 1989, 1991, 1992, 2018];
const SATELLITE_LAYER='Satellite';
let currentLayer = YEARS[0];

mapboxgl.accessToken = 'pk.eyJ1IjoicnZpbGltIiwiYSI6ImNqZ2Nic2R5czNncWwyd241djdwODIyOGgifQ.YwmNuS4UDs0Q27LBHvLg7w';

var map = new mapboxgl.Map({
  container: 'map',
  style: BASE_STYLE,
  center: [-79.3738487, 43.6486135],
  zoom: 13
});
map.addControl(new mapboxgl.NavigationControl({showCompass: false}), 'bottom-right');
map.addControl(new mapboxgl.GeolocateControl({
  positionOptions: {
    enableHighAccuracy: true
  }
}), 'bottom-right');
let marker;

map.on('load', () => {
  window.map = map;

  // Turn off transitions for now; may want to revisit whether these are helpful.
  for (const year of YEARS) {
    map.setPaintProperty('' + year, 'raster-fade-duration', 0);
  }
  showYear(currentLayer);
});

function cleanupVisibility() {
  // Hide all layers which aren't the current year.
  for (const year of YEARS) {
    const layer = '' + year;
    if (layer !== currentLayer) {
      map.setLayoutProperty(layer, 'visibility', 'none');
    }
  }
}

function showYear(year) {
  const newLayer = '' + year;
  if (newLayer !== currentLayer) {
    $('#year').text(year);
    currentLayer = newLayer
    map.setLayoutProperty(currentLayer, 'visibility', 'visible');
    map.moveLayer(currentLayer, 'landuse_overlay_national_park');  // move to, below labels
    // hide the old layer after things have settled to avoid a visual glitch.
    window.setTimeout(cleanupVisibility, 1000);
  }
}

function changeYear(delta) {
  const index = $('#slider').slider('value');
  const newIndex = (index + YEARS.length + delta) % YEARS.length;
  const year = YEARS[newIndex];
  showYear(year);
  $('#slider').slider('value', newIndex);
}

$('#slider').slider({
  min: 0,
  max: YEARS.length - 1,
  value: 0,
  slide: (event, ui) => {
    const index = ui.value;
    showYear(YEARS[index]);
  }
});

$('#prev-year').on('click', () => changeYear(-1));
$('#next-year').on('click', () => changeYear(+1));

let timerId;

$('#pause').on('click', () => {
  window.clearInterval(timerId);
  timerId = null;
  $('#pause').hide();
  $('#play').show();
});

$('#play').on('click', () => {
  changeYear(+1);
  timerId = window.setInterval(() => {
    changeYear(+1);
  }, 2000);
  $('#play').hide();
  $('#pause').show();
});

let labelsVisible = false;
function setLabelVisibility() {
  const visibility = labelsVisible ? 'visible' : 'none';
  for (const label of LABEL_LAYERS) {
    map.setLayoutProperty(label, 'visibility', visibility);
  }
}

let satelliteVisible = false;
function setSatelliteVisibility() {
  const visibility = satelliteVisible ? 'visible' : 'none';
  map.setLayoutProperty(SATELLITE_LAYER, 'visibility', visibility);
}

$('#show-labels').on('change', function() {
  labelsVisible = $(this).is(':checked');
  setLabelVisibility();
});
$('#show-satellite').on('change', function() {
  satelliteVisible = $(this).is(':checked');
  setSatelliteVisibility();
});

$('#location-search').on('keypress', function(e) {
  if (e.which !== 13) return;

  const address = $(this).val();
  $.getJSON('https://maps.googleapis.com/maps/api/geocode/json', {
    address,
    key: 'AIzaSyCS3o6gGDBx16T0OQtb_2wJRuxlcFjfnyA',
    // This is a bit tight to avoid a bug with how Google geocodes "140 Yonge".
    bounds: '43.598284,-79.448761|43.712376, -79.291565'
  }).done(response => {
    const latLng = response.results[0].geometry.location;
    if (marker) {
      marker.setMap(null);
    }

    const {lng, lat} = latLng;
    marker = new mapboxgl.Marker()
      .setLngLat([lng, lat])
      .addTo(map);

    map.setCenter([lng, lat]);
    map.setZoom(15);
  }).fail(e => {
    console.error(e);
    ga('send', 'event', 'link', 'address-search-fail');
  })
});
