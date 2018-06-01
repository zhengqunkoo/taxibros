// Javacript file is "dynamically" generated using django's template generation
//
// Note: This example requires that you consent to location sharing when
// prompted by your browser. If you see the error "The Geolocation service
// failed.", it means you probably did not give permission for the browser to
// locate you.
var map, heatmap, infoWindow;
var pointArray;

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    zoom: 12,
    center: {lat: 1.3521, lng: 103.8198},
    mapTypeId: 'roadmap'
  });

  pointArray = new google.maps.MVCArray(getPoints());

  heatmap = new google.maps.visualization.HeatmapLayer({
    data: pointArray,
    map: map
  });

  infoWindow = new google.maps.InfoWindow;
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

function getPoints() {
  return [
    {% for coord in coordinates %}
      new google.maps.LatLng({{ coord.lat }}, {{ coord.long }}),
    {% endfor %}
  ];
}

function showNearby() {
    // Try HTML5 geolocation.
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(position) {
        var pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };

        infoWindow.setPosition(pos);
        infoWindow.setContent('Location found.');
        infoWindow.open(map);
        map.setCenter(pos);
        map.setZoom(16);

        $.ajax({
            url: "{% url 'visualize:genLoc' %}",
            data: {
                pos: JSON.stringify(pos)
            },
            dataType: 'json',
            success: function(data) {
                pointArray.clear();
                var coordinates = data.coordinates;
                var average_dist = data.average_dist;
                var number = data.number;
                var day_stats = data.day_stats;
                //Filling up map
                var length = coordinates.length;
                var coord;
                for (var i=0; i<length; i++) {
                  coord = coordinates[i];
                  pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
                }
                //Load stats
                if (number != 0) { //Gets around zero division error
                    document.getElementById('average_dist').innerHTML = average_dist;
                }
                document.getElementById('num').innerHTML = number;


                //Draw circle
                var circle = new google.maps.Circle({
                  strokeColor: '#FF7F50',
                  strokeOpacity: 0.2,
                  strokeWeight: 2,
                  fillColor: '#FF7F50',
                  fillOpacity: 0.05,
                  map: map,
                  center: pos,
                  radius: 500,
                });
                //Draw chart
                drawChart(day_stats);


            },
            error: function(rs, e) {
                alert("Failed to reach {% url 'visualize:genLoc' %}.");
            }
        });
      }, function() {
        handleLocationError(true, infoWindow, map.getCenter());
      });
    } else {
      // Browser doesn't support Geolocation
      handleLocationError(false, infoWindow, map.getCenter());
    }
}

function minutesChange(e) {
  // Asynchronously update maps with serialized coordinates.
  var minutes = e.value;
  if (minutes.hasOwnProperty('newValue')) {
    minutes = minutes.newValue;
  }
  $.ajax({
      url: "{% url 'visualize:genTime' %}",
      data: {
          minutes: minutes,
      },
      dataType: 'json',
      success: function(data) {
          pointArray.clear();
          var coordinates = data.coordinates
          var length = coordinates.length;
          var coord;
          for (var i=0; i<length; i++) {
            coord = coordinates[i];
            pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
          }
      },
      error: function(rs, e) {
          alert("Failed to reach {% url 'visualize:genTime' %}.");
      }
  });
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(browserHasGeolocation ?
                        'Error: The Geolocation service failed.' :
                        'Error: Your browser doesn\'t support geolocation.');
  infoWindow.open(map);
}


function drawChart(day_stats) {
    var height = 420,
        barWidth = 10;
    var margin = {top: 20, right: 10, bottom: 20, left: 40};
    height = height - margin.top - margin.bottom;

    var y = d3.scaleLinear()
        .domain([0, d3.max(day_stats)])
        .range([height,0]);
    var yAxis = d3.axisLeft(y)
        .scale(y)
        .ticks(10, "s");
    var chart = d3.select(".chart")
        .attr("height", height);
    chart.attr("width", barWidth * day_stats.length);

    var rect = chart.selectAll("g")
        .data(day_stats)
      .enter().append("rect")
        .attr("transform", function(d, i) { return "translate(" + (margin.left + (i * barWidth)) + ",0)"; })
        .attr("y", height) //To initialize bar outside chart
        .attr("width", barWidth - 1)
        .attr("height", function(d) {return height-y(d);});

    rect.transition()
        .delay(function(d, i) {return i * 10; })
        .attr("y",function(d) {return y(d);});


    chart.append("g")
        .attr("transform", "translate(" + margin.left+ ",0)")
        .call(yAxis);


}
