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

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');


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
  {% if not mobile %}
  drawChart();
  {% endif %}
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
   * Unpack data from API and pass to updateStats.
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

  // If no optional arguments, retrieve latest data with ajax.
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

        // Update table with latest data.
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
        updateStats(path_time, path_dist, total_dist, number, best_road, best_road_coords);
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
    updateStats(path_time, path_dist, total_dist, number, best_road, best_road_coords);
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
  // Only function that calls with isCreate set is autocomplete event listener.
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

function initAutocomplete(input, isPickup) {
  /**
   * Call the Place API with string as input. API returns list of places.
   * @param input: HTML input element to put the search box at.
   *   Hidden info from returned place (e.g. name) appends to input element.
   * @param isPickup: if true, autocomplete has functionality of pickupLocation.
   *   If false, autocomplete has functionality of arrivalLocation.
   *   In both cases,
   *     Store location in respective cell in table.
   *     Get both pickup and arrival locations, if not null, call calcRoute. 
   * @return undefined.
   */

  // Return only geocoding results.
  // Restrict the search to a specific country.
  // Restrict the search to the bounds.
  var options = {
    types: ['geocode'],
    componentRestrictions: {country: 'sg'},
    strictBounds: true,
  };

  // Create the search box and link it to the UI element.
  var autocomplete = new google.maps.places.Autocomplete(input, options);

  // Set the data fields to return when the user selects a place.
  autocomplete.setFields(['name', 'geometry']);

  // Listen for the event fired when the user selects a prediction and retrieve
  // more details for that place.
  autocomplete.addListener('place_changed', function() {
    var place = autocomplete.getPlace();
    var tr = $('#' + input.getAttribute('id')).closest('tr');

    if (isPickup) {

      // If isPickup, call genLoc with isCreate circle true.
      // Store pickupPos in table's tr's nth-child(9).
      var pickupPos = place.geometry.location;
      var arrivalPos = tr.children('td:nth-child(20)').find('.hide')[0].innerHTML;
      genLoc(pickupPos, locationRadius, locationMinutes, input.getAttribute('id'), true);
      tr.children('td:nth-child(9)').find('.hide').html(pickupPos.lat() + ',' + pickupPos.lng());
      if (arrivalPos) {
        calcRoute(pickupPos, parseLatLngMaps(arrivalPos), tr);
      }
    } else {

      // Else, isArrival.
      // Store arrivalPos in table's tr's nth-child(20).
      var arrivalPos = place.geometry.location;
      var pickupPos = tr.children('td:nth-child(9)').find('.hide')[0].innerHTML;
      tr.children('td:nth-child(20)').find('.hide').html(arrivalPos.lat() + ',' + arrivalPos.lng());
      if (pickupPos) {
        calcRoute(parseLatLngMaps(pickupPos), arrivalPos, tr);
      }
    }

    // Put place name in input, and in innerText for table.
    // Update table.
    input.innerText = place.name;
    input.value = place.name;
    updateTable();

    // Mobile does not have enough space for chart, do not display chart.
    {% if not mobile %}
    appearContainerChart();
    {% endif %}
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

var mus = new Mus();

window.onload = function() {
  mus.release();
  mus.record();
  console.log("Recording mouse data.");
}

window.onunload = function() {
  mus.stop();
  console.log("Stop recording mouse data.");

  // https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
  fetch("{% url 'mouse:set_record' %}", {
    method: "POST",
    mode: "cors",
    credentials: "include",
    body: JSON.stringify(mus.getData()),
    headers: {
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  }).catch(err => {
    console.error(err);
  });
  mus.release();
}

$(function() {

  // Initialize autocomplete inside container-slider with location calls
  isPickup = true;
  initAutocomplete($('.pac-input-slider')[0], isPickup);
  initAutocomplete($('.pac-input-slider')[1], isPickup);
});
