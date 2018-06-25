$(document).ready(function() {
  $('#slider').click(function() {
      var rightVal = $("#container-itinerary").css("right");
      if (rightVal == '10px'){
          $('#container-itinerary').stop().animate({right:"-50%"}, 500);
          $('#slider').prop("value","<<");

      } else {
          $('#container-itinerary').stop().animate({right:"10px"},500);
          $('#slider').prop("value",">>");
      }
  });
});
