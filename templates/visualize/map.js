// Javacript file is "dynamically" generated using django's template generation
//
// Note: This example requires that you consent to location sharing when
// prompted by your browser. If you see the error "The Geolocation service
// failed.", it means you probably did not give permission for the browser to
// locate you.
var map, heatmap, infoWindow;
var pointArray, intensityArray;
var pickups = {}, pickupIdLatest = 0;

var locationCenter, locationCircle;
var directionsService;
var directionsDisplay;

function initMap() {
    directionsService = new google.maps.DirectionsService;
    directionsDisplay = new google.maps.DirectionsRenderer;
    map = new google.maps.Map(document.getElementById('map'), {
    zoom: 12,
    center: new google.maps.LatLng(1.3521, 103.8198),
    mapTypeId: 'roadmap',
    mapTypeControl:false,
    fullscreenControl: false,
    streetViewControl:false,
    zoomControl: false,
    styles: [
    {
        "featureType": "landscape",
        "stylers": [
            {
                "hue": "#FFBB00"
            },
            {
                "saturation": 43.400000000000006
            },
            {
                "lightness": 37.599999999999994
            },
            {
                "gamma": 1
            }
        ]
    },
    {
        "featureType": "road.highway",
        "stylers": [
            {
                "hue": "#FFC200"
            },
            {
                "saturation": -61.8
            },
            {
                "lightness": 45.599999999999994
            },
            {
                "gamma": 1
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "stylers": [
            {
                "hue": "#FF0300"
            },
            {
                "saturation": -100
            },
            {
                "lightness": 51.19999999999999
            },
            {
                "gamma": 1
            }
        ]
    },
    {
        "featureType": "road.local",
        "stylers": [
            {
                "hue": "#FF0300"
            },
            {
                "saturation": -100
            },
            {
                "lightness": 52
            },
            {
                "gamma": 1
            }
        ]
    },
    {
        "featureType": "water",
        "stylers": [
            {
                "hue": "#0078FF"
            },
            {
                "saturation": -13.200000000000003
            },
            {
                "lightness": 2.4000000000000057
            },
            {
                "gamma": 1
            }
        ]
    },
    {
        "featureType": "poi",
        "stylers": [
            {
                "hue": "#00FF6A"
            },
            {
                "saturation": -1.0989010989011234
            },
            {
                "lightness": 11.200000000000017
            },
            {
                "gamma": 1
            }
        ]
    }
]
  });

  pointArray = new google.maps.MVCArray(getPoints());
  intensityArray = new Array();

  heatmap = new google.maps.visualization.HeatmapLayer({
    data: pointArray,
    map: map
  });

  infoWindow = new google.maps.InfoWindow;
  secondInfoWindow = new google.maps.InfoWindow;

  drawChart();
}

function setLocation(pos) {
  locationCenter = pos;
}

function unsetLocation() {
  locationCenter = undefined;
}

function getPoints() {
  /**
   * Use Django templating to loop over coordinates (passed from context).
   * @return: array of LatLngs.
   */
  return [
    {% for coord in coordinates %}new google.maps.LatLng({{ coord.lat }},{{ coord.lng }}),{% endfor %}
  ];
}

function genLoc(pos, radius, minutes, pickupId, isCreate, path_geom, path_instructions, coordinates, number, best_road, best_road_coords, path_time, path_dist, total_dist, journey_geom) {
  /**
   * Show real taxi distribution at a location and time.
   * @param pickupId: associative array key to be handled by updatePickupId.
   *
   * Call Taxibros API at visualize/genLoc.js with @params:
   *   pos: center of circle of interest.
   *   radius: radius of circle of interest.
   *   minutes: time of interest.
   * Unpack data from API and pass to genLocHandleData.
   *
   * Alternatively, if optional arguments, don't call Taxibros API.
   * @return: undefined.
   */
  // Set global location variables.
  pickupIdLatest = pickupId
  setLocation(pos);
  map.setCenter(pos);

  // Update global @param locationCircle to be same pos, radius as local @param circle.
  // Pass circle to updatePickup for storage in associative array.
  // Important: do this before ajax query.

  // TODO not efficient
  // Create new circle here (isCreate==true) because unset old circle.
  var circle = updateLocationCircle(pos, radius, pickupId, isCreate);

  // If no optional arguments, perform ajax call.
  if (arguments.length == 5) {

    $.ajax({
      url: "{% url 'visualize:genLoc' %}",
      data: {
        lat: pos.lat,
        lng: pos.lng,
        radius: radius,
        minutes: minutes
      },
      dataType: 'json',
      success: function(data) {
        coordinates = data.coordinates;
        total_dist = data.total_dist;
        number = data.number;
        best_road = data.best_road;
        best_road_coords = data.best_road_coords;
        path_geom = data.path_geom;
        path_instructions = data.path_instructions;
        path_time = data.path_time;
        path_dist = data.path_dist;

        // Update table with latest information.
        var tr = $('#' + pickupId).closest('tr');
        tr.children('td:nth-child(7)').find('.hide').html(path_geom);
        tr.children('td:nth-child(8)').find('.hide').html(path_instructions);
        tr.children('td:nth-child(9)').find('.hide').html(pos.lat() + ',' + pos.lng());
        tr.children('td:nth-child(10)').find('.hide').html(coordinates.join(';'));
        tr.children('td:nth-child(11)').find('.hide').html(radius);
        tr.children('td:nth-child(12)').find('.hide').html(minutes);
        tr.children('td:nth-child(13)').find('.hide').html(number);
        tr.children('td:nth-child(14)').find('.hide').html(best_road);
        tr.children('td:nth-child(15)').find('.hide').html(best_road_coords.lat + ',' + best_road_coords.lng);
        tr.children('td:nth-child(16)').find('.hide').html(path_time);
        tr.children('td:nth-child(17)').find('.hide').html(path_dist);
        tr.children('td:nth-child(18)').find('.hide').html(total_dist);
        updateTable();

        updatePickup(circle, pickupId, isCreate, path_geom, path_instructions, coordinates, journey_geom);
        genLocHandleData(path_time, path_dist, total_dist, number, best_road, best_road_coords);
        // Show better location.
        if (best_road_coords.lat != null && best_road_coords.lat != null) {
          infoWindow.setPosition(best_road_coords);
          infoWindow.setContent('Better location');
        }
      },
      error: function(rs, e) {
        console.log("Failed to reach {% url 'visualize:genLoc' %}.");
      }
    });
  } else {
    updatePickup(circle, pickupId, isCreate, path_geom, path_instructions, coordinates, journey_geom);
    genLocHandleData(path_time, path_dist, total_dist, number, best_road, best_road_coords);
    // Show better location.
    if (best_road_coords.lat != null && best_road_coords.lat != null) {
      infoWindow.setPosition(best_road_coords);
      infoWindow.setContent('Better location');
    }
  }
}

function updatePickup(circle, pickupId, isCreate, path_geom, path_instructions, coordinates, journey_geom) {
  /**
   * Visualize data.
   * Create google map objects (polylineArrays, circles, pointArrays).
   * Store objects in associative array, keyed with @param pickupId.
   * Replace objects, by unsetPickup function, on key collision.
   * @return: undefined.
   */
  unsetPickup(pickupId, isCreate);
  var walkpath = decode(path_geom, pickupId);
  var journey = decode(journey_geom, pickupId);
  if (walkpath) {
    walkpath.setMap(map);
  }
  if (journey) {
    journey.setMap(map);
  }

  // Push into pointArray and save in associative array.
  var pickupPointArray = new google.maps.MVCArray();
  coordinates.forEach(coord => {
    pickupPointArray.push(new google.maps.LatLng(coord[0], coord[1]));
  });
  pickups[pickupId] = [walkpath, circle, pickupPointArray, journey];

  // TODO this is costly when many old pickups.
  // maybe invert? one global pointArray bound to hashmap: key latlng, value pickupId.
  // on change / delete pickupId, remove from hashmap and thus from pointArray.

  // Push rest of points from associative array.
  pointArray.clear();
  for (var key in pickups) {
    pickups[key][2].forEach(latlng => {
      pointArray.push(latlng);
    });
  }
}

function decode(encoded, pickupId){
  /**
   * Decode the @param encoded polyline.
   * https://developers.google.com/maps/documentation/utilities/polylinealgorithm
   * @return walkpath: google Polyline object, or null if @param encoded is null.
   */
  if (encoded == null) {
    return null;
  }
  var index = 0, len = encoded.length;
  var lat = 0, lng = 0;
  var polylineArray = new google.maps.MVCArray();

  while (index < len) {
    var b, shift = 0, result = 0;
    do {
      b = encoded.charAt(index++).charCodeAt(0) - 63; //finds ascii and substract it by 63
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    var dlat = ((result & 1) != 0 ? ~(result >> 1) : (result >> 1));
    lat += dlat;
    shift = 0;
    result = 0;
    do {
      b = encoded.charAt(index++).charCodeAt(0) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    var dlng = ((result & 1) != 0 ? ~(result >> 1) : (result >> 1));
    lng += dlng;

    polylineArray.push(new google.maps.LatLng(( lat / 1E5),( lng / 1E5)));
  }

  var walkpath = new google.maps.Polyline({
    path: polylineArray,
    geodesic: true,
    strokeColor: "FF000",
    strokeOpacity: 1.0,
    strokeWeight:2
  })
  return walkpath;
}

function setMouseResize(circle, pickupId) {
  /**
   * Add event listeners to center and radius changes.
   * @return: undefined.
   */
  google.maps.event.addListener(circle, 'center_changed', function() {
    setLocation(circle.getCenter());
    locationRadius = circle.getRadius();
    pickupIdLatest = pickupId;
    genLoc(locationCenter, locationRadius, locationMinutes, pickupIdLatest, true);
  });
  google.maps.event.addListener(circle, 'radius_changed', function() {
    setLocation(circle.getCenter());
    locationRadius = circle.getRadius();
    pickupIdLatest = pickupId;
    genLoc(locationCenter, locationRadius, locationMinutes, pickupIdLatest, true);
  });
}

function updateLocationCircle(pos, radius, pickupId, isCreate) {
  /**
   * Create or update global @param locationCircle if @param pos or radius differ.
   * Reposition map to fit circle bounds.
   * @return: new local circle, if @param isCreate set, else undefined.
   */
  if (locationCircle === undefined) {

    // Create new circle.
    locationCircle = new google.maps.Circle({
      strokeColor: '#FF7F50',
      strokeOpacity: 0.2,
      strokeWeight: 2,
      fillColor: '#FF7F50',
      fillOpacity: 0.05,
      map: map,
      center: pos,
      radius: radius,
    });

  } else {

    // Update center.
    if (locationCircle.getCenter().lat() !== pos.lat()
      || locationCircle.getCenter().lng() !== pos.lng()) {
      locationCircle.setCenter(pos);
    }

    // Update radius.
    if (locationCircle.getRadius() != radius) {
      locationCircle.setRadius(radius);
    }
  }

  // Show entire locationCircle.
  map.fitBounds(locationCircle.getBounds());

  // No need fit bounds here.
  // Only function that calls with isCreate set is searchBox event listener.
  // That listener already fits bounds on returned search places.
  if (isCreate) {
    var circle = new google.maps.Circle({
      strokeColor: '#FF7F50',
      strokeOpacity: 0.2,
      strokeWeight: 2,
      fillColor: '#FF7F50',
      fillOpacity: 0.05,
      map: map,
      center: pos,
      radius: radius,
      editable: true,
    });

    // Add event handlers.
    setMouseResize(circle, pickupId);

    return circle;
  }
}

function initAutocomplete(input, isCallGenLoc) {
  /**
   * Call the Place API with string as input. API returns list of places.
   * @param input: HTML input element to put the search box at.
   *   Hidden info from returned place (e.g. name) appends to input element.
   * @param isCallGenLoc: if true, call genLoc if one place returned from API.
   *   If false, call calcRoute.
   * @return undefined.
   */
  // Create the search box and link it to the UI element.
  var searchBox = new google.maps.places.SearchBox(input);

  // Bias the SearchBox results towards current map's viewport.
  map.addListener('bounds_changed', function() {
    searchBox.setBounds(map.getBounds());
  });

  var markers = [];
  // Listen for the event fired when the user selects a prediction and retrieve
  // more details for that place.
  searchBox.addListener('places_changed', function() {
    var places = searchBox.getPlaces();

    if (places.length == 0) {
      return;
    }

    // Clear out the old markers.
    markers.forEach(function(marker) {
      marker.setMap(null);
    });
    markers = [];

    var bounds = new google.maps.LatLngBounds();
    if (places.length > 1) {

      // If more than one place, for each place, get the icon, name and location.
      places.forEach(function(place) {
        if (!place.geometry) {
          console.log("Returned place contains no geometry");
          return;
        }
        var icon = {
          url: place.icon,
          size: new google.maps.Size(71, 71),
          origin: new google.maps.Point(0, 0),
          anchor: new google.maps.Point(17, 34),
          scaledSize: new google.maps.Size(25, 25)
        };

        // Create a marker for each place.
        markers.push(new google.maps.Marker({
          map: map,
          icon: icon,
          title: place.name,
          position: place.geometry.location
        }));

        if (place.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(place.geometry.viewport);
        } else {
          bounds.extend(place.geometry.location);
        }
      });
      map.fitBounds(bounds);
    } else {

      // Else if only one place, perform genLoc.
      // Create list element.
      var place = places[0];
      if (isCallGenLoc) {
        genLoc(place.geometry.location, locationRadius, locationMinutes, input.getAttribute('id'), true);
      } else {

        // Extract origin from hidden info in table.
        // Calc route only if info is not null.
        var tr = $('#' + input.getAttribute('id')).closest('tr');
        var pickupPos = tr.children('td:nth-child(9)').find('.hide')[0].innerHTML;
        if (pickupPos) {
          var parsedLatLng = parseLatLng(pickupPos);
          origin = new google.maps.LatLng(parsedLatLng[0], parsedLatLng[1]);
          calcRoute(origin, place.geometry.location, tr);
        }
      }
      input.innerText = place.name;
      input.value = place.name;
      updateTable();
    }
  });
}

function unsetPickup(pickupId, isCreate) {
  /**
   * @param pickupId: associative array key.
   * Unset walkpath, circle, and taxi coords, corresponding to pickupId.
   */
  if (pickupId in pickups) {
    var pickup = pickups[pickupId];
    var walkpath = pickup[0];
    var circle = pickup[1];
    var pointArray = pickup[2];
    var journey = pickup[3];
    if (walkpath) {
      unsetMapObj(walkpath);
    }
    if (isCreate) {
      unsetMapObj(circle);
    }
    pointArray.clear();
    if (journey) {
      unsetMapObj(journey);
    }
  }
}

function unsetMapObj(obj) {
  /**
   * Remove google map objects from map.
   * @param obj: google map object.
   */
  obj.setMap(null);
  obj = null;
}

$(document).ready(function() {

  // Initialize autocomplete with location calls
  isCallGenLoc = true;
  initAutocomplete($('.pac-input-slider')[0], isCallGenLoc);
  initAutocomplete($('.pac-input-slider')[1], isCallGenLoc);
});
