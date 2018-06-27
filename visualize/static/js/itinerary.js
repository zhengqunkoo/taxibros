$(document).ready(function() {
  $('#slider').click(function() {
      var rightVal = $("#container-itinerary").css("right");
      if (rightVal == '10px'){
          $('#container-itinerary').stop().animate({right:"-50%"}, 500);
          document.querySelector('.arrow').style.transform = ("rotate(-135deg)");
      } else {
          $('#container-itinerary').stop().animate({right:"10px"},500);
          document.querySelector('.arrow').style.transform = ("rotate(45deg)");
      }
  });
});
