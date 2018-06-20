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
=======
var locationEnabled = false, walkpathIdLatest, curLocation;
var locationCircle = null; // google maps Circle
>>>>>>> 4821612d2b1e65d1c0681cdaf300e6b400d38630

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

function genLoc(pos, radius, minutes, walkpathId) {

  // Set global location variables.
  locationEnabled = true;
  walkpathIdLatest = walkpathId
  curLocation = pos;

  map.setCenter(pos);
  map.setZoom(16);

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

      coordinates.forEach(function(coord) {
        pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
      });
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

      // Delete locationCircle if not null
      if (locationCircle) {
        locationCircle.setMap(null);
        locationCircle = null;
      }

      // Draw locationCircle
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

      appearStats();
      infoWindow.setPosition(best_road_coords);
      infoWindow.setContent('Better location');

      $('#walkpathGeom' + walkpathId).html(path_geom);
      $('#walkpathInstructions' + walkpathId).html(path_instructions);
      decode(path_geom, walkpathId);
    },
    error: function(rs, e) {
      console.log("Failed to reach {% url 'visualize:genLoc' %}.");
    }
  });
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
      genLoc(pos, 500, 0, 'showNearby'); // genLoc in 500 meters, current time
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

function genSliderCallback(minutes, url, successCallback) {

  // Asynchronously update maps.
  $.ajax({
    url: url,
    data: {
        minutes: minutes,
    },
    dataType: 'json',
    success: successCallback,
    error: function(rs, e) {
        console.log("Failed to reach " + url + ".");
    }
  });
}

function genTimeSliderChange(minutes) {
  if (locationEnabled) {
    // genTimeSliderChange should not have own walkpathId.
    // If locationEnabled, then genLoc was called outside genTimeSliderChange.
    // genTimeSliderChange then changes time in context of this location.
    // So, path of location should change as well.
    // Replace old path with path at new time.
    console.log(walkpathIdLatest);
    genLoc(curLocation, 500, minutes, walkpathIdLatest);
  } else {
    genSliderCallback(minutes, "{% url 'visualize:genTime' %}", function(data) {
      pointArray.clear();
      data.coordinates.forEach(function(coord) {
        pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
      });
    });
  }
}

function genHeatmapSliderChange(minutes) {
  genSliderCallback(minutes, "{% url 'visualize:genHeatmap' %}", function(data) {
    pointArray.clear();
    while (intensityArray.length) { intensityArray.pop(); }
    data.heattiles.forEach(function(d) {
      pointArray.push(new google.maps.LatLng(d[1], d[2]));
      intensityArray.push(d);
    });
  });
}

function genHeatmapIntensitySliderChange(value) {

  // Filters on intensityArray. Assume intensityArray defined.
  // Only change pointArray if intensityArray has elements.
  if (intensityArray.length != 0) {
    var intensities = intensityArray.filter(d => d[0] >= value);
    pointArray.clear();
    intensities.forEach(function(d) {
      pointArray.push(new google.maps.LatLng(d[1], d[2]));
    });
  }
}

function drawChart() {

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

           // Typical action to be performed when the document is ready:
           var response = JSON.parse(this.responseText);
           var day_stats = response.day_stats;
           var title = response.chart_title;
           var height = 210,
               width = 300;
           var margin = {top: 20, right: 10, bottom: 30, left: 40};

           var chart = d3.select(".chart")
               .attr("height", height);
           chart.attr("width", width);

           height = height - margin.top - margin.bottom;
           width = width - margin.left - margin.right;
           var barWidth = width/day_stats.length;

           var y = d3.scaleLinear()
               .domain([0, d3.max(day_stats)])
               .range([height,0]);
           var yAxis = d3.axisLeft(y)
               .scale(y)
               .ticks(5, "s");

           var parseTime = d3.timeParse("%I:%M %p");
           var startTime = parseTime("06:00 AM");
           var endTime = parseTime("05:00 AM");

           var x = d3.scaleTime().domain([startTime, endTime]).range([0,width]);
           var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%I:%M %p")).tickArguments(d3.timeMinute.every(60));



           var rect = chart.selectAll("g")
               .data(day_stats)
             .enter().append("rect")
               .attr("transform", function(d, i) { return "translate(" + (margin.left + (i * barWidth)) + ",0)"; })
               .attr("y", height) //To initialize bar outside chart
               .attr("width", barWidth - 1)
               .attr("height", function(d) {return height-y(d);});

           rect.transition()
               .delay(function(d, i) {return i * 100; })
               .attr("y",function(d) {return y(d);});


           chart.append("g")
               .attr("transform", "translate(" + margin.left+ ",0)")
               .call(yAxis);
           chart.append("g")
                .attr("transform", "translate(" + margin.left + "," + height + ")")
              .call(xAxis)
              .selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");

            $("#chart-title").text(title);
        }
    };
    xhttp.open("GET", "{% url 'visualize:chart' %}", true);
    xhttp.send();


}

function decode(encoded, walkpathId){
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

  unsetWalkpath(walkpathId);

  var walkpath = new google.maps.Polyline({
    path: polylineArray,
    geodesic: true,
    strokeColor: "FF000",
    strokeOpacity: 1.0,
    strokeWeight:2
  })
  walkpath.setMap(map);

  walkpaths[walkpathId] = walkpath;
  console.log(walkpaths);
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
        genLoc(place.geometry.location, 500, 0, input.getAttribute('id')); // genLoc in 500 meters, current time
      }
      input.innerText = place.name;
      input.value = place.name;
      updateTable();
    }
  });
}

function createPacInput(cell, isCallGenLoc, innerText) {
  var input = document.createElement('input');
  input.setAttribute('id', 'pac-input' + pacInputCount);
  input.setAttribute('class', 'controls td-height');
  input.setAttribute('type', 'text');
  input.setAttribute('placeholder', 'Search Google Maps');
  cell.appendChild(input);
  if (innerText !== undefined) {
    input.value = innerText;
    input.innerText = innerText;
  }
  initAutocomplete(input, isCallGenLoc);
  pacInputCount++;
}

function createDatetimepicker(cell, innerText) {
  var input = document.createElement('input');
  input.setAttribute('type', 'text');
  input.setAttribute('class', 'form-control td-height');
  input.setAttribute('id', 'datetimepicker' + datetimepickerCount);
  input.setAttribute('placeholder', 'Pick a date');
  cell.appendChild(input);
  if (innerText !== undefined) {
    $('#datetimepicker' + datetimepickerCount).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss',
      date: innerText
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
    });
    input.innerText = innerText;
  } else {
    $('#datetimepicker' + datetimepickerCount).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss'
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
    });
  }
  datetimepickerCount++;
}

function createHiddenText(id, innerText) {
  var span = document.createElement('span');
  span.setAttribute('class', 'hide');
  span.setAttribute('id', id);
  if (innerText !== undefined) {
    span.innerText = innerText;
  }
  return span;
}

function createDeleteRowButton(cell, innerText) {
  var input = document.createElement('input');
  input.setAttribute('type', 'button');
  input.setAttribute('class', 'deleteRow td-height');
  input.setAttribute('value', 'Delete');
  cell.appendChild(input);
  cell.appendChild(createHiddenText('', innerText));
}

function addRow(pickupLocationInnerText, pickupTimeInnerText, arrivalLocationInnerText, arrivalTimeInnerText, walkpathGeomInnerText, walkpathInstructionsInnerText) {
  var row = itineraryTable.getElementsByTagName('tbody')[0].insertRow(-1);
  var pickupLocationCell = row.insertCell(0);
  var pickupTimeCell = row.insertCell(1);
  var arrivalLocationCell = row.insertCell(2);
  var arrivalTimeCell = row.insertCell(3);
  var deleteRowButtonCell = row.insertCell(4);
  var walkpathGeomCell = row.insertCell(5);
  var walkpathInstructionsCell = row.insertCell(6);

  createDeleteRowButton(deleteRowButtonCell, '#pac-input' + pacInputCount);
  walkpathGeomCell.appendChild(createHiddenText('walkpathGeompac-input' + pacInputCount, walkpathGeomInnerText));
  walkpathInstructionsCell.appendChild(createHiddenText('walkpathInstructionspac-input' + pacInputCount, walkpathInstructionsInnerText));

  createPacInput(pickupLocationCell, true, pickupLocationInnerText);
  createDatetimepicker(pickupTimeCell, pickupTimeInnerText);
  createPacInput(arrivalLocationCell, false, arrivalLocationInnerText);
  createDatetimepicker(arrivalTimeCell, arrivalTimeInnerText);
  updateTable();
}

function deleteRow(){
  var tr = $(this).closest('tr');
  unsetWalkpath(tr.find('.hide')[0].innerText);
  tr.remove();
  updateTable();
}

function removeStats() {
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
        debugger;
        var display_duration = null;
        var duration = null;
        directionsDisplay.setDirections(result);
        if (result.routes[0].legs[0].hasOwnProperty("duration_in_traffic")) {
            display_duration = result.routes[0].legs[0].duration_in_traffic["text"]
            duration = result.routes[0].legs[0].duration_in_traffic["value"];
            var raw_duration = result.routes[0].legs[0].duration["value"];
            var waiting_duration = duration - raw_duration;
            computeTime(duration, display_duration);
            calcCost(waiting_duration);
        } else {
            display_duration = result.routes[0].legs[0].duration["text"]
            duration = result.routes[0].legs[0].duration["value"];
            computeTime(duration, display_duration);
            calcCost(0);
        }
    }
  });
}

function computeTime(duration, display_duration) {

}

function updateTable() {
  $('#itineraryTable').trigger('update')
  $('#itineraryTable').tableExport().update({
    headings: true,
    footers: true,
    formats: ['csv'],
    filename: 'taxibros',
    bootstrap: true,
    position: "bottom",
    ignoreCols: 4,
    trimWhitespace: false
  });
}

function importFromCsvChange(e) {
  Papa.parse(e.target.files[0], {
    error: function(err, file, inputElem, reason) {
      alert('Papaparse ' + err + reason);
    },
    complete: function(e) {
      importToItineraryTable(e.data);
    }
  });
}

function importToItineraryTable(data) {
  $("#itineraryTable > tbody").empty();
  data.slice(1).forEach(row =>
    addRow.apply(null, row)
  );
  updateTable();
}

function unsetWalkpath(walkpathId) {
  // If walkpathId exists, unset path.
  if (walkpathId in walkpaths) {
    var walkpathOld = walkpaths[walkpathId];
    walkpathOld.setMap(null);
    walkpathOld = null;
  }
}


$(document).ready(function() {
  $('#addRow').on('click', function() {
    addRow();
  });
  $('#itineraryTable').on('click', '.deleteRow', deleteRow);
  $('#importFromCsv').on('change', importFromCsvChange);
  TableExport.prototype.formatConfig.csv.buttonContent = 'Export';

  $('#itineraryTable').tablesorter({
    widthFixed: true,
    widgets: [
      'zebra',
    ],
  }).tablesorterPager({
      container: $("#pager"),
  });

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

  addRow();
});
