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

function showPosition(position) {
  var pos = new google.maps.LatLng(
    position.coords.latitude,
    position.coords.longitude
  );
  infoWindow.setPosition(pos);
  infoWindow.setContent('Location found.');
  infoWindow.open(map);
  genLoc(pos, locationRadius, locationMinutes, 'showNearby', true);
}

var browserGeolocationFail = function(error) {
  var message;
  switch(error.code) {
    case error.PERMISSION_DENIED:
      message = "User denied the request for Geolocation."
      if(error.message.indexOf("Only secure origins are allowed") == 0) {
        geolocatePosition();
      }
      break;
    case error.POSITION_UNAVAILABLE:
      message = "Location information is unavailable."
      geolocatePosition();
      break;
    case error.TIMEOUT:
      message = "The request to get user location timed out."
      geolocatePosition();
      break;
    case error.UNKNOWN_ERROR:
      message = "An unknown error occurred."
      geolocatePosition();
      break;
  }
  handleLocationError(infoWindow, map.getCenter(), "Error " + error.code + ": " + message);
};

function showNearby() {
  /**
   * Show HTML5 geolocated position in infoWindow.
   * @return: undefined.
   */
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, browserGeolocationFail);
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(infoWindow, map.getCenter());
  }
}

function geolocatePosition() {
  $.post( "https://www.googleapis.com/geolocation/v1/geolocate?key={{ GOOGLEMAPS_SECRET_KEY }}", function(pos) {
    var position = {coords: {latitude: pos.location.lat, longitude: pos.location.lng}}
    showPosition(position);
  }).fail(function(err) {
    console.log("API Geolocation error: "+err);
  });
};

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

function toggleContainerItineraryButton() {
  $itineraryButton = "<a id = 'itineraryButton' href='#' class='footer-link'>\
              <i class='fas fa-clipboard-list'></i><span onclick='toggleContainerItinerary()'class='footer-text'>Itinerary</span>\
          </a>";
  if (nowLater == 'later'){
    $('.mobile-bottom-bar').append($itineraryButton);
  } else {
    $('#itineraryButton').remove();
  }
}

function toggleContainerItinerary(){
    if (currentDisplay != "itinerary") {
        undisplayAll()
        $('#container-itinerary').toggle();
        currentDisplay = "itinerary";
    } else {
        $('#container-itinerary').hide();
        currentDisplay = null;
    }
}


/*
function toggleContainerChart() {
  var val = $('#container-chart').css("left");
  if (val == '-1000px'){
    appearContainerChart();
  } else {
    disappearContainerChart();
  }
}
*/



function toggleNowLaterSetting() {
    if (nowLater == "now") {
        nowLater = "later";
    } else {
        nowLater = "now";
    }
}

function toggleNowLater(){
  undisplayBottom();
  toggleNowLaterSetting();
  //LATER SERVICE
  toggleContainerItineraryButton();
  //toggleContainerChart();

}

function disappearStats() {
    //Function for container stats to disappear to the side
  $('#container-stats').css("right", "-100%");
}




function toggleStats() {
  if (currentDisplay != "stats") {
      undisplayAll()
      $('#container-stats').toggle();
      currentDisplay = "stats";
  } else {
      $('#container-stats').hide();
      currentDisplay = null;
  }
}

function toggleSliders() {
  if (currentDisplay!="slider") {
      if (nowLater == "later") {
          undisplayAll();
          $('#container-slider-later').toggle();
      } else {
          undisplayAll();
          $('#container-slider-now').toggle();
      }
      currentDisplay="slider";
  } else {
      currentDisplay=null;
      $('.container-slider').hide();
  }
}

function undisplayAll() {
    $('#menuToggle > input:checked').prop('checked',false);
    undisplayBottom();
}
function undisplayBottom() {
    $('.bottom-display').hide();
}

$(function() {
    $('#menuToggle > input[type=checkbox]').change(function(){
        if($(this).is(':checked')) {
            undisplayBottom();
        }
    });
});
