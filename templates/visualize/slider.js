$('#genTime').slider({
  formatter: function (value) {
    var date = new Date();
    return new Date(date - value*60000);
  }
}).on('{{ SLIDE_EVENT }}', genTimeSliderChange);

$('#genHeatmap').slider({
  formatter: function (value) {
    var date = new Date();
    return new Date(date - value*60000);
  }
}).on('{{ SLIDE_EVENT }}', genHeatmapSliderChange);

$('#genHeatmapIntensity').slider({
  formatter: function (value) {
    return value;
  }
}).on('{{ SLIDE_EVENT }}', genHeatmapIntensitySliderChange);
