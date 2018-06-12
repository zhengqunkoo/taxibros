var date = new Date();
var MS_PER_MINUTE = 60000;

dateSlider('#genTime', genTimeSliderChange);
dateSlider('#genHeatmap', genHeatmapSliderChange);

$('#genHeatmapIntensity').slider({
  formatter: function(value) {
    return value;
  }
}).on('{{ SLIDE_EVENT }}', genHeatmapIntensitySliderChange);

$('#datetimepicker').datetimepicker({
  date: date
})

function minutesToDate(minutes) {
  return new Date(date - minutes * MS_PER_MINUTE);
}

function dateToMinutes(date) {
  return (new Date() - date) / MS_PER_MINUTE;
}

function dateSlider(sliderName, sliderChangeCallback) {
  $(sliderName).slider({
    formatter: minutesToDate
  }).on('{{ SLIDE_EVENT }}', function(e) {
    sliderChangeCallback(e);
    $('#datetimepicker').datetimepicker('date', minutesToDate(e.value.newValue));
  });
}
