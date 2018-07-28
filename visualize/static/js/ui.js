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
    navigator.geolocation.watchPosition(showPosition, browserGeolocationFail);
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
  $('#container-stats').stop().animate({right: "-50%"},1200);
}

function appearStats() {
  $('#container-stats').stop().animate({right: "0%"},400);
}

function disappearContainerChart() {
  $('#container-chart').stop().animate({left:"-1000px"},500);
}

function appearContainerChart() {
  $('#container-chart').stop().animate({left:"28px"},500);
}
