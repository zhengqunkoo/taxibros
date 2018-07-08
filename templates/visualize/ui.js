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
   * Show geolocated position in infoWindow.
   * @return: undefined.
   */
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var pos = new google.maps.LatLng(
        position.coords.latitude,
        position.coords.longitude
      );

      infoWindow.setPosition(pos);
      infoWindow.setContent('Location found.');
      infoWindow.open(map);
      genLoc(pos, locationRadius, locationMinutes, 'showNearby', true);
    }, function() {
      handleLocationError(true, infoWindow, map.getCenter());
    });
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(false, infoWindow, map.getCenter());
  }
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  /**
   * Writes an error message to @param infoWindow.
   */
  infoWindow.setPosition(pos);
  infoWindow.setContent(browserHasGeolocation ?
                        'Error: The Geolocation service failed.' :
                        'Error: Your browser doesn\'t support geolocation.');
  infoWindow.open(map);
}

function toggleNowLater(){
    //LATER SERVICE
    //Toggle container-itinerary

    var leftVal,rightVal;
    rightVal = $("#container-itinerary").css("right");
    //Toggle container itinerary value
    if (rightVal == '-1000px'){
        $('#container-itinerary').stop().animate({right:"10px"},500);
        document.querySelector('.arrow').style.transform = ("rotate(45deg)");
    } else {
        $('#container-itinerary').stop().animate({right:"-1000px"}, 500);
        document.querySelector('.arrow').style.transform = ("rotate(-135deg)");
    }
    //Toggle container chart now value
    rightVal = $("#container-slider-later").css("right");
    if (rightVal == '-1000px') {
        $('#container-slider-later').stop().animate({right:"5%"});
    } else {
        $('#container-slider-later').stop().animate({right:"-1000px"});
    }
    //Toggle container-chart
    leftVal = $('#container-chart').css("left");
    if (leftVal == '-1000px'){
        $('#container-chart').stop().animate({left:"28px"},500);
    } else {
        $('#container-chart').stop().animate({left:"-1000px"},500);
    }

    //NOW SERVICE
    rightVal = $('#container-slider-now').css("right");
    if (rightVal == '-1000px') {
        $('#container-slider-now').stop().animate({right:"5%"});
    } else {
        $('#container-slider-now').stop().animate({right:"-1000px"});
    }
}
