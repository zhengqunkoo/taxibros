// Update global date on all callbacks.
var date = new Date();
var MS_PER_MINUTE = 60000;

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
