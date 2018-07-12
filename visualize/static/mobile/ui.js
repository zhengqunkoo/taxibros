var nowLater = "now";
var currentDisplay = null;
function toggleUi() {
  $('#container-ui').toggle();
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

function toggleHeatmap() {
  heatmap.setMap(heatmap.getMap() ? null : map);
}

function showNearby() {
  /**
   * Show HTML5 geolocated position in infoWindow.
   * @return: undefined.
   */
  if (navigator.geolocation) {
    navigator.geolocation.watchPosition(function(position) {
      var pos = new google.maps.LatLng(
        position.coords.latitude,
        position.coords.longitude
      );

      infoWindow.setPosition(pos);
      infoWindow.setContent('Location found.');
      infoWindow.open(map);
      genLoc(pos, locationRadius, locationMinutes, 'showNearby', true);
    }, function(error) {
      var message;
      switch(error.code) {
        case error.PERMISSION_DENIED:
          message = "User denied the request for Geolocation."
          break;
        case error.POSITION_UNAVAILABLE:
          message = "Location information is unavailable."
          break;
        case error.TIMEOUT:
          message = "The request to get user location timed out."
          break;
        case error.UNKNOWN_ERROR:
          message = "An unknown error occurred."
          break;
      }
      handleLocationError(infoWindow, map.getCenter(), "Error " + error.code + ": " + message);
    });
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(infoWindow, map.getCenter());
  }
}

function handleLocationError(infoWindow, pos, errorMessage) {
  /**
   * Writes an error message to @param infoWindow.
   */
  infoWindow.setPosition(pos);
  infoWindow.setContent((errorMessage === undefined) ?
                        'Error: Your browser doesn\'t support geolocation.' :
                         errorMessage);
  infoWindow.open(map);
}

function toggleContainerItinerary() {
  var val = $("#container-itinerary").css("right");
  if (val == '-1000px'){
    $('#container-itinerary').stop().animate({right:"10px"},500);
    document.querySelector('.arrow').style.transform = ("rotate(45deg)");
  } else {
    $('#container-itinerary').stop().animate({right:"-1000px"}, 500);
    document.querySelector('.arrow').style.transform = ("rotate(-135deg)");
  }
}

function toggleContainerSliderLater() {
  var val = $("#container-slider-later").css("right");
  if (val == '-1000px') {
    $('#container-slider-later').stop().animate({right:"5%"});
  } else {
    $('#container-slider-later').stop().animate({right:"-1000px"});
  }
}

function toggleContainerChart() {
  var val = $('#container-chart').css("left");
  if (val == '-1000px'){
    appearContainerChart();
  } else {
    disappearContainerChart();
  }
}

function toggleContainerSliderNow() {
  var val = $('#container-slider-now').css("right");
  if (val == '-1000px') {
    $('#container-slider-now').stop().animate({right:"5%"});
  } else {
    $('#container-slider-now').stop().animate({right:"-1000px"});
  }
}

function toggleNowLater(){
  //LATER SERVICE
  toggleContainerItinerary();
  toggleContainerSliderLater();
  toggleContainerChart();

  //NOW SERVICE
  toggleContainerSliderNow();
}

function disappearStats() {
    //Function for container stats to disappear to the side
  $('#container-stats').css("right", "-100%");
}




function toggleStats() {
  var statsHtml = "        <!--Local statistics(Right)-->\
          <div id = 'container-stats'>\
              <button id='remove-stats' onclick='disappearStats()'type='button' class='close' aria-label='Close'>\
              <span aria-hidden='true'>&times;</span></button>\
              <div class = 'container-bg'></div>\
              <table id = 'stats-table'>\
                  <tr>\
                      <th> Statistics of taxis within 500m:</th>\
                  <tr>\
                      <td> Number of taxis:</td>\
                      <td id='num'> '-' </td>\
                  </tr>\
                  <tr>\
                      <td>Average distance:</td>\
                      <td id='average_dist'> '-'</td>\
                  </tr>\
              </table>\
          </div>";
  if (currentDisplay != "stats") {
      $('#bottom-display').html(statsHtml);
      currentDisplay = "stats";
  } else {
      $('#bottom-display').html("");
      currentDisplay = null;
  }
}

function toggleSliders() {
    var nowHTML = "    <div class='container-slider' id='container-slider-now'>\
            <div class = 'container-bg-container'>\
                <div class = 'container-bg'></div>\
            </div>\
            <div class = 'container-slider-inner'>\
                <div> VISUALIZATION SLIDERS (NOW)</div>\
                <div> Slide across time </div>\
                <input type='range' id='genTime' data-slider-id='genTimeSlider' type='text' data-slider-min='0' data-slider-max='5' data-slider-step='1' data-slider-value='0'><br>\
                <input id='pac-input-slider' class='controls td-height pac-input-slider' type='text' placeholder='Search Google Maps'>\
            </div>\
        </div>";
  var laterHtml = "    <div class='container-slider' id='container-slider-later'>\
          <div class = 'container-bg-container'>\
              <div class = 'container-bg'></div>\
          </div>\
          <div class = 'container-slider-inner'>\
              <div> VISUALIZATION SLIDERS (LATER)</div>\
              <div> Slide across heatmap </div>\
              <input type='range' id='genHeatmap' data-slider-id='genHeatmapSlider' type='text' data-slider-min='0' data-slider-max='1440' data-slider-step='5' data-slider-value='0'><br>\
              <div> Slide across heatmap intensity</div>\
              <input type='range' id='genHeatmapIntensity' data-slider-id='genHeatmapIntensitySlider' type='text' data-slider-min='1' data-slider-max='10' data-slider-step='1' data-slider-value='0'><br>\
              <div>Slide location radius</div>\
              <input type='range' id='genLocationRadius' data-slider-id='genLocationRadiusSlider' type='text' data-slider-min='50' data-slider-max='5000' data-slider-step='10' data-slider-value='500'><br>\
              <div class='input-group date' id='datetimepicker'>\
                  <input type='text' class='form-control'/>\
                  <span class='input-group-addon'>\
                  <span class='glyphicon glyphicon-calendar'></span>\
                  </span>\
              </div>\
              <input id='pac-input-slider' class='controls td-height pac-input-slider' type='text' placeholder='Search Google Maps'>\
          </div>\
      </div>";
  if (currentDisplay!="slider") {
      if (nowLater == "later") {
          $('#bottom-display').html(nowHtml);
          dateSlider('#genHeatmap', genHeatmapSliderChange);
          $('#genHeatmapIntensity').slider({
            formatter: function(value) {
              return value;
            }
          }).on('{{ SLIDE_EVENT }}', function(e) {
            genHeatmapIntensitySliderChange(genSliderValue(e))
          });
          $('#genLocationRadius').slider({
            formatter: function(value) {
              return value;
            }
          }).on('change', function(e) {
            genLocationRadiusSliderChange(genSliderValue(e))
          }).on('slideStop', function(e) {
            genLocationRadiusSliderStop(genSliderValue(e))
          });

          $('#datetimepicker').datetimepicker({
            format: 'YYYY/MM/DD HH:mm:ss',
            date: date
          }).on('dp.hide', pickDate);

      } else {
          $('#bottom-display').html(laterHtml);
          //dateSlider('#genTime', genTimeSliderChange);
      }
      currentDisplay="slider";
  } else {
      $('#bottom-display').html("");
      currentDisplay=null;
  }
}
