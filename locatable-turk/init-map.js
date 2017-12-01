function initMap() {
  const geocoder = new google.maps.Geocoder();
  var map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 43.652505, lng: -79.384424},
    zoom: 13
  });
  var marker = null;
  var card = document.getElementById('pac-card');
  var input = document.getElementById('pac-input');

  function updateHiddenFieldWithLatLng(latLng) {
    latLngStr = latLng.lat() + ',' + latLng.lng();
    var json = JSON.stringify({"latLng":latLngStr});
    document.getElementById('latLng').setAttribute('value', json);
    document.getElementById('loc-yes').setAttribute('checked', true);
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

  var infowindow = new google.maps.InfoWindow();
  var infowindowContent = document.getElementById('infowindow-content');
  infowindow.setContent(infowindowContent);

  marker = new google.maps.Marker({
    map: null,  // Hidden initially
    position: map.getCenter(),
    draggable: true,
    animation: google.maps.Animation.DROP
  });

  google.maps.event.addListener(marker, 'dragend', function() {
    updateHiddenFieldWithLatLng(marker.getPosition());
  });

  autocomplete.addListener('place_changed', function() {
    infowindow.close();
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
        }
      });
      // window.alert("No details available for input: '" + place.name + "'");
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
  });

  document.querySelector('#loc-yes').addEventListener('change', () => {
    marker.setMap(map);
  });
  document.querySelector('#loc-maybe').addEventListener('change', () => {
    marker.setMap(map);
  });
  document.querySelector('#loc-no').addEventListener('change', () => {
    marker.setMap(null);
  })
}

document.getElementById('date-start').addEventListener('keypress', () => {
  document.getElementById('date-yes').setAttribute('checked', true);
});

(function() {
  // Hide empty bullets.
  const lis = document.querySelectorAll('#metadata li');
  for (const li of lis) {
    if (li.textContent === '') {
      li.parentNode.removeChild(li);
    }
  }
})();

document.getElementById('submit').addEventListener('click', (event) => {
  // setCustomValidity should be set to the empty string in order to recover from previous error messages
  const dateRangeIsSet = [
      ...document.querySelectorAll('#date-range-radio > input')
  ].reduce((acc, curr) => (acc ? acc : curr.checked), false);
  if (!dateRangeIsSet) {
    document.getElementById('date-yes')
        .setCustomValidity('Must record whether this photo is datable or not.');
  } else {
    document.getElementById('date-yes').setCustomValidity('');
  }
  const geolocatableIsSet = [
      ...document.querySelectorAll('#geolocatable-radio > input')
  ].reduce((acc, curr) => (acc ? acc : curr.checked), false);
  if (!geolocatableIsSet) {
    document.getElementById('loc-yes')
      .setCustomValidity('Must record whether this photo is geocodable or not.');
  } else {
    document.getElementById('loc-yes').setCustomValidity('')
  }
  if (document.getElementById('date-yes').checked === true) {
    const isDatesEmpty =
      document.getElementById('date-start').value.length === 0 &&
      document.getElementById('date-end').value.length === 0;
    if (isDatesEmpty) {
      document
        .getElementById('date-start')
        .setCustomValidity('Must enter a start year or end year.');
    } else {
      document
        .getElementById('date-start')
        .setCustomValidity('');
    }
  }
});
