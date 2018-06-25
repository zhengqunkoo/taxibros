// Update global date on all callbacks.
var date = new Date();
var MS_PER_MINUTE = 60000;
var locationRadius = 500, locationMinutes = 0;

dateSlider('#genTime', genTimeSliderChange);
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

function pickDate(e) {
  /**
   * Reset sliders to middle.
   * Set min and max value of sliders relative to picked date.
   * Call genHeatmapChange.
   *   Assume when users pick date, they want heatmaps from long ago.
   */

  // Update global date on all callbacks.
  date = new Date();

  // Convert date to minutes (to be set for sliders).
  var minutes = dateToMinutes(e.date);
  var genTime = $('#genTime');
  var genHeatmap = $('#genHeatmap');

  var genTimeRange = genTime.data('sliderMax') - genTime.data('sliderMin');
  genTime.slider({
    min: minutes - genTimeRange/2,
    max: minutes + genTimeRange/2,
  });
  genTime.slider('setValue', minutes);

  var genHeatmapRange = genHeatmap.data('sliderMax') - genHeatmap.data('sliderMin');
  genHeatmap.slider({
    min: minutes - genHeatmapRange/2,
    max: minutes + genHeatmapRange/2,
  });
  genHeatmap.slider('setValue', minutes);

  genHeatmapSliderChange(minutes);
}

function minutesToDate(m) {
  /**
   * Convert @param m to date, relative to global date variable.
   */
  return new Date(date - m * MS_PER_MINUTE);
}

function dateToMinutes(d) {
  /**
   * Convert @param d to minutes, relative to global date variable.
   * @return minutes: integer.
   */
  return ((date - d) / MS_PER_MINUTE) | 0;
}

function genSliderValue(e) {
  /**
   * Extract value from slider event.
   */
  var value = e.value;
  if (value.hasOwnProperty('newValue')) {
    value = value.newValue;
  }
  return value;
}

function dateSlider(sliderName, sliderChangeCallback) {
  /**
   * Create new slider.
   * Bind slider event to datetimepicker date value.
   */
  $(sliderName).slider({
    formatter: minutesToDate
  }).on('{{ SLIDE_EVENT }}', function(e) {

    // Update global date on all callbacks.
    date = new Date();
    sliderChangeCallback(genSliderValue(e));
    $('#datetimepicker').datetimepicker('date', minutesToDate(e.value.newValue));
  });
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
  locationMinutes = minutes;
  if (locationCenter !== undefined) {
    // genTimeSliderChange should not have own pickupId.
    // If locationCenter defined, then genLoc was called outside genTimeSliderChange.
    // genTimeSliderChange then changes time in context of this location.
    genLoc(locationCenter, locationRadius, locationMinutes, pickupIdLatest, false);
  } else {
    genSliderCallback(minutes, "{% url 'visualize:genTime' %}", function(data) {
      pointArray.clear();
      data.coordinates.forEach(function(coord) {
        pointArray.push(new google.maps.LatLng(coord[0], coord[1]));
      });
    });
  }
}

function genLocationRadiusSliderChange(radius) {
  locationRadius = radius;
  if (locationCenter !== undefined) {
    updateLocationCircle(locationCenter, locationRadius, pickupIdLatest, false);
  }
}

function genLocationRadiusSliderStop(radius) {
  locationRadius = radius;
  if (locationCenter !== undefined) {
    genLoc(locationCenter, locationRadius, locationMinutes, pickupIdLatest, true);
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
