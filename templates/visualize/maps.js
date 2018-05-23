// Javacript file is "dynamically" generated using django's template generation
var map, heatmap;
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

function minutesChange(e) {
  // Asynchronously update maps with serialized coordinates.
  $.ajax({
      url: "{% url 'visualize:gen.js' %}",
      data: {
          minutes: e.value,
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
          alert("Failed to reach {% url 'visualize:gen.js' %}.");
      }
  });
}
