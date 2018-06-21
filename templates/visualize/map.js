// Javacript file is "dynamically" generated using django's template generation
//
// Note: This example requires that you consent to location sharing when
// prompted by your browser. If you see the error "The Geolocation service
// failed.", it means you probably did not give permission for the browser to
// locate you.
var map, heatmap, infoWindow;
var pointArray, intensityArray;
var pickups = {}, pickupIdLatest = 0;

// TODO wrap curLocation and locationEnabled in function so that
// curLocation is defined when locationEnabled.
var locationEnabled = false, curLocation, curLocationCircle;

function initMap() {
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

      // Update table with latest information.
      var tr = $('#' + pickupId).closest('tr');
      tr.children('td:nth-child(6)').find('.hide').html(path_geom);
      tr.children('td:nth-child(7)').find('.hide').html(path_instructions);
      tr.children('td:nth-child(8)').find('.hide').html(pos.lat() + ';' + pos.lng());
      tr.children('td:nth-child(9)').find('.hide').html(coordinates);
      updateTable();

      // Unset and replace pickup, if pickupId exists.
      unsetPickup(pickupId);
      var walkpath = decode(path_geom, pickupId);
      walkpath.setMap(map);
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

function decode(encoded, pickupId){
  /**
   * return walkpath: google Polyline object.
   */
    if (encoded == null) {
        return
    }
    //Decoding the encoded path geometry

    var index = 0, len = encoded.length;
    var lat = 0, lng = 0;
    var polylineArray = new google.maps.MVCArray();
    while (index < len) {
        var b, shift = 0, result = 0;
        do {

    b = encoded.charAt(index++).charCodeAt(0) - 63;//finds ascii                                                                                    //and substract it by 63
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

function setMouseResize(circle) {
  google.maps.event.addListener(circle, 'center_changed', function() {
    locationEnabled = true;
    curLocation = circle.getCenter();
    // Show entire circle.
    map.fitBounds(circle.getBounds());
    genLoc(curLocation, locationRadius, locationMinutes, pickupIdLatest);
  });
  google.maps.event.addListener(circle, 'radius_changed', function() {
    locationRadius = circle.getRadius();
    map.fitBounds(circle.getBounds());
    genLoc(curLocation, locationRadius, locationMinutes, pickupIdLatest);
  });
}

function updateLocationCircle(pos, radius, isCreate) {
  if (curLocationCircle === undefined) {

    // Create new circle.
    curLocationCircle = new google.maps.Circle({
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
    setMouseResize(curLocationCircle);
  } else {

    // Update center.
    if (curLocationCircle.getCenter() != pos) {
      curLocationCircle.setCenter(pos);
    }

    // Update radius.
    if (curLocationCircle.getRadius() != radius) {
      curLocationCircle.setRadius(radius);
    }
  }

  // Show entire locationCircle.
  map.fitBounds(curLocationCircle.getBounds());

  if (isCreate) {
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
