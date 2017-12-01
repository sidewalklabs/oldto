// Styles for Google Maps. These de-emphasize features on the map.
export var MAP_STYLE = [
    // to remove buildings
    {"stylers": [ {"visibility": "off" } ] },
    {"featureType": "water","stylers": [{"visibility": "simplified"} ] },
    {"featureType": "poi","stylers": [ {"visibility": "simplified"} ]},
    {"featureType": "transit","stylers": [{ "visibility": "off"}] },
    { "featureType": "landscape","stylers": [ { "visibility": "simplified" } ] },
    { "featureType": "road", "stylers": [{ "visibility": "simplified" } ] },
    { "featureType": "administrative",  "stylers": [{ "visibility": "simplified" } ] },
    // end remove buildings
    {
        "featureType": "administrative",
        "elementType": "labels",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "administrative.country",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "administrative.province",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry",
        "stylers": [
            {
                "visibility": "on"
            },
            {
                "color": "#e3e3e3"
            }
        ]
    },
    {
        "featureType": "landscape.natural",
        "elementType": "labels",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "color": "#cccccc"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry",
        "stylers": [
            {
                "color": "#FFFFFF"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels",
        "stylers": [
            {
                "color": "#94989C"
            },
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    }
];
