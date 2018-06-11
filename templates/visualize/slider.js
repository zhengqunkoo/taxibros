$('#genTime').slider({
  formatter: function (value) {
    return value;
  }
}).on('{{ SLIDE_EVENT }}', genTimeSliderChange);

$('#genHeatmap').slider({
  formatter: function (value) {
    return value;
  }
}).on('{{ SLIDE_EVENT }}', genHeatmapSliderChange);
