/* global mapboxgl */

import 'mapbox-gl-compare';

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

var map2 = new mapboxgl.Map({
  container: 'map2',
  style: BASE_STYLE,
  center: [-79.3738487, 43.6486135],
  zoom: 13
})

new mapboxgl.Compare(map, map2, {
  // mousemove: true // Optional. Set to true to enable swiping during cursor movement.
});

let marker;

map.on('load', () => {
  window.map = map;

  map.setLayoutProperty('Satellite', 'visibility', 'none');
  for (const year of YEARS) {
    map.setPaintProperty('' + year, 'raster-fade-duration', 0);
    map2.setPaintProperty('' + year, 'raster-fade-duration', 0);
  }

  showYear('1947', map);
  showYear('2018', map2);
});

function showYear(year, map) {
  const newLayer = '' + year;

  $('#year').text(year);
  const currentLayer = newLayer
  map.setLayoutProperty(currentLayer, 'visibility', 'visible');
  map.moveLayer(currentLayer, 'landuse_overlay_national_park');  // move to, below labels
  for (const year of YEARS) {
    const layer = '' + year;
    if (layer !== currentLayer) {
      map.setLayoutProperty(layer, 'visibility', 'none');
    }
  }
}

let labelsVisible = false;
function setLabelVisibility() {
  const visibility = labelsVisible ? 'visible' : 'none';
  for (const label of LABEL_LAYERS) {
    map.setLayoutProperty(label, 'visibility', visibility);
    map2.setLayoutProperty(label, 'visibility', visibility);
  }
}

$('#year-select').on('change', function() {
  const year = $(this).val();
  showYear(year, map);
});

$('#show-labels').on('change', function() {
  labelsVisible = $(this).is(':checked');
  setLabelVisibility();
});

$('#location-search').on('keypress', function(e) {
  if (e.which !== 13) return;

  document.activeElement.blur();  // hides keyboard for kiosk

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
