// Javacript file is "dynamically" generated using django's template generation
//
// Note: This example requires that you consent to location sharing when
// prompted by your browser. If you see the error "The Geolocation service
// failed.", it means you probably did not give permission for the browser to
// locate you.
var map, heatmap, infoWindow;
var pointArray, intensityArray;
var walkpaths = {};
var pacInputCount = 0, datetimepickerCount = 0;
var pickups = {}, pickupIdLatest = 0;
var locationEnabled = false, walkpathIdLatest, curLocation;
var curLocationCircle;
var locationCircle = null; // google maps Circle
var directionsService;
var directionsDisplay;

function initMap() {
    directionsService = new google.maps.DirectionsService();
    directionsDisplay = new google.maps.DirectionsRenderer();
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

function toggleHeatmap() {
  heatmap.setMap(heatmap.getMap() ? null : map);
}

function changeGradient() {
  var gradient = [
    'rgba(0, 255, 255, 0)',
    'rgba(0, 255, 255, 1)',
    'rgba(0, 191, 255, 1)',
    'rgba(0, 127, 255, 1)',
    'rgba(0, 63, 255, 1)',
    'rgba(0, 0, 255, 1)',
    'rgba(0, 0, 223, 1)',
    'rgba(0, 0, 191, 1)',
    'rgba(0, 0, 159, 1)',
    'rgba(0, 0, 127, 1)',
    'rgba(63, 0, 91, 1)',
    'rgba(127, 0, 63, 1)',
    'rgba(191, 0, 31, 1)',
    'rgba(255, 0, 0, 1)'
  ]
  heatmap.set('gradient', heatmap.get('gradient') ? null : gradient);
}

function changeRadius() {
  heatmap.set('radius', heatmap.get('radius') ? null : 20);
}

function changeOpacity() {
  heatmap.set('opacity', heatmap.get('opacity') ? null : 0.2);
}

function resetLocation() {
  locationEnabled = false;
}

function getPoints() {
  return [
    {% for coord in coordinates %}new google.maps.LatLng({{ coord.lat }},{{ coord.lng }}),{% endfor %}
  ];
}

function genLoc(pos, radius, minutes, pickupId) {

  // Set global location variables.
  locationEnabled = true;
  pickupIdLatest = pickupId
  curLocation = pos;

  map.setCenter(pos);

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
      pointArray.clear();
      var coordinates = data.coordinates;
      var total_dist = data.total_dist;
      var number = data.number;
      var best_road = data.best_road;
      var best_road_coords = data.best_road_coords;
      var path_geom = data.path_geom;
      var path_instructions = data.path_instructions;
      var path_time = data.path_time;
      var path_dist = data.path_dist;

      //Load stats
      if (number != 0) { //Gets around zero division error
        document.getElementById('average_dist').innerHTML = Math.trunc(total_dist/number) + "m";
      }
      document.getElementById('num').innerHTML = number;

      //Add, modify, or delete data depending on condition
      if ($('#a').length == 0) {
          $('#stats-table tr:last').after('<tr id = "a"><th>Better Waiting Location</th></tr>');
          $('#stats-table tr:last').after('<tr id = "b"><td>Time to travel</td><td id = "path-time">"-"</td></tr>');
          $('#stats-table tr:last').after('<tr id = "c"><td>Distance of travel</td><td id = "path-dist">"-"</td></tr>');
      }
      if (path_time==null) {
          $('#a').remove();
          $('#b').remove();
          $('#c').remove();
      } else {
          $('#path-time').html(path_time + "s");
          $('#path-dist').html(path_dist + "m");
      }

      appearStats();
      infoWindow.setPosition(best_road_coords);
      infoWindow.setContent('Better location');

      $('#walkpathGeom' + pickupId).html(path_geom);
      $('#walkpathInstructions' + pickupId).html(path_instructions);
      $('#pickupLatLng' + pickupId).html(pos.lat() + ';' + pos.lng());
      $('#pickupTaxiCoords' + pickupId).html(coordinates);
      var walkpath = decode(path_geom, pickupId);

      var locationCircle = updateLocationCircle(pos, radius, true);

      // Push into pointArray and save in associative array.
      var pickupPointArray = new google.maps.MVCArray();
      coordinates.forEach(coord => {
        pickupPointArray.push(new google.maps.LatLng(coord[0], coord[1]));
        pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
      });
      pickups[pickupId] = [walkpath, locationCircle, pickupPointArray];

      // TODO this is costly when many old pickups.
      // maybe invert? one global pointArray bound to hashmap: key latlng, value pickupId.
      // on change / delete pickupId, remove from hashmap and thus from pointArray.

      // Push rest of points from associative array.
      for (var key in pickups) {
        if (key != pickupId) {
          pickups[key][2].forEach(latlng => {
            pointArray.push(latlng);
          });
        }
      }
    },
    error: function(rs, e) {
      console.log("Failed to reach {% url 'visualize:genLoc' %}.");
    }
  });
}

function updateLocationCircle(pos, radius, isReturn) {
  if (curLocationCircle === undefined || curLocationCircle.getCenter() != pos) {
    // If undefined or position changed.
    curLocationCircle = new google.maps.Circle({
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
    curLocationCircle.setRadius(radius);
  }

  // Show entire locationCircle.
  map.fitBounds(curLocationCircle.getBounds());

  if (isReturn) {
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
    return locationCircle;
  }
}

function showNearby() {
  // Try HTML5 geolocation.
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var pos = new google.maps.LatLng(
        position.coords.latitude,
        position.coords.longitude
      );

      infoWindow.setPosition(pos);
      infoWindow.setContent('Location found.');
      infoWindow.open(map);
      genLoc(pos, locationRadius, locationMinutes, 'showNearby');
    }, function() {
      handleLocationError(true, infoWindow, map.getCenter());
    });
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(false, infoWindow, map.getCenter());
  }
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(browserHasGeolocation ?
                        'Error: The Geolocation service failed.' :
                        'Error: Your browser doesn\'t support geolocation.');
  infoWindow.open(map);
}

function initAutocomplete(input, isCallGenLoc) {
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
        genLoc(place.geometry.location, locationRadius, locationMinutes, input.getAttribute('id'));
      }
      input.innerText = place.name;
      input.value = place.name;
      updateTable();
    }
  });
}

function unsetPickup(pickupId) {
  // If pickupId exists, unset path, circle, and taxi coords.
  if (pickupId in pickups) {
    var pickup = pickups[pickupId];
    var walkpath = pickup[0];
    var locationCircle = pickup[1];
    var pointArray = pickup[2];
    unsetMapObj(walkpath);
    unsetMapObj(locationCircle);
    pointArray.clear();
  }
}

function disappearStats() {
    //Function for container stats to disappear to the side
  $('#container-stats').stop().animate({right: "-50%"},1200);
}

function appearStats() {
    //Function for container stats to appear on RHS of screen
  $('#container-stats').stop().animate({right: "0%"},400);
}


function calcRoute(start_lat, start_lng, end_lat, end_lng) {
    var request = {
        origin: new google.maps.LatLng(start_lat,start_lng),
        destination: new google.maps.LatLng(end_lat,end_lng),
        travelMode: 'DRIVING',
        drivingOptions: {
            departureTime: new Date(Date.now()),  // for the time N milliseconds from now.
            trafficModel: 'bestguess'
        }
    };
    directionsService.route(request, function(result, status) {
    if (status == 'OK') {
        var display_duration = null;
        var duration = null;
        var waiting_duration = 0;
        var display_distance;
        var distance;
        directionsDisplay.setDirections(result);
        if (result.routes[0].legs[0].hasOwnProperty("duration_in_traffic")) {
            //Duration in traffic is only displayed when there is enough traffic
            display_duration = result.routes[0].legs[0].duration_in_traffic["text"]
            duration = result.routes[0].legs[0].duration_in_traffic["value"];
            var raw_duration = result.routes[0].legs[0].duration["value"];

        } else {
            display_duration = result.routes[0].legs[0].duration["text"]
            duration = result.routes[0].legs[0].duration["value"];
        }
        waiting_duration = 0.2*duration;
        if (raw_duration > duration) {
            waiting_duration = 0.1 * duration;
        }

        display_distance = result.routes[0].legs[0].distance["text"];
        distance = result.routes[0].legs[0].distance["value"]
        calcCost(waiting_duration, distance);
        displayTaxiStats(duration, display_duration, display_distance);
        appearStats();

    }


  });
}


function displayTaxiStats(duration, display_duration, display_distance) {
    //Add, modify, or delete data depending on condition
    if ($('#d').length == 0) {
        $('#stats-table tr:last').after('<tr id = "d"><th>Taxi Route Information</th></tr>');
        $('#stats-table tr:last').after('<tr id = "e"><td>Time of travel</td><td id = "taxi-time">"-"</td></tr>');
        $('#stats-table tr:last').after('<tr id = "f"><td>Distance of travel</td><td id = "taxi-dist">"-"</td></tr>');

    }
    if (display_duration==null) {
        $('#d').remove();
        $('#e').remove();
        $('#f').remove();
    } else {
        $('#taxi-time').html(display_duration);
        $('#taxi-dist').html(display_distance);
    }
}

function calcCost(waiting_time, distance) {

    $.ajax({
      url: "{% url 'visualize:cost' %}",
      data: {
        time: waiting_time,
        distance: distance,
      },
      dataType: 'json',
      success: function(data) {

            var costs = data.cost;
            displayCosts(costs);

        },
        error: function(rs, e) {
          console.log("Failed to reach {% url 'visualize:cost' %}.");
        }
    });
}
function displayCosts(costs) {
    //Add, modify, or delete data depending on condition
    if ($('#g').length == 0) {
        $('#stats-table tr:last').after('<tr id = "g"><td>Cost of travel(low)</td><td id = "taxi-cost-l">"-"</td></tr>');
        $('#stats-table tr:last').after('<tr id = "h"><td>Cost of travel(high)</td><td id = "taxi-cost-h">"-"</td></tr>');
    }
    if (costs==null) {
        $('#g').remove();
        $('#h').remove();
    } else {
        $('#taxi-cost-l').html("$" + parseFloat(costs[0]/100).toFixed(2));
        $('#taxi-cost-h').html("$" + parseFloat(costs[1]/100).toFixed(2));
    }
}
function unsetMapObj(obj) {
  obj.setMap(null);
  obj = null;
}


$(document).ready(function() {
  $('#slider').click(function() {
      var leftVal = $("#container-itinerary").css("left");
      if (leftVal == '10px'){
          $('#container-itinerary').stop().animate({left:"-50%"}, 500);
          $('#slider').prop("value",">>");

      } else {
          $('#container-itinerary').stop().animate({left:"10px"},500);
          $('#slider').prop("value","<<");
      }
  });
});
