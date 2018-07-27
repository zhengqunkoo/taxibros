// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

// These HTTP methods do not require CSRF protection.
function csrfSafeMethod(method) { return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method)); }

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

var mus = new Mus();
mus.setPlaybackSpeed(mus.speed.SLOW);

var toggleRecord = function() {
  if (mus.isPlaying()) return;
  if (!mus.isRecording()) {
    document.getElementById("status").innerHTML = "Recording";
    document.getElementById("recording").innerHTML = "Stop recording";

    // Clean variables before recording new information.
    mus.release();
    mus.record();

  } else {
    document.getElementById("status").innerHTML = "Stand by";
    document.getElementById("recording").innerHTML = "Start recording";
    mus.stop();

    // Send recorded data to database, then reset mus.
    $.ajax({
      url: "{% url 'mouse:set_record' %}",
      data: JSON.stringify(mus.getData()),
      method: "POST",
      success: function(data) {
        console.log("Sent mouse data to {% url 'mouse:set_record' %}.");
      },
      error: function(rs, e) {
        console.log("Failed to reach {% url 'mouse:set_record' %}.");
      }
    });
    mus.release();

  }
};

var play = function(record_id) {
  if (mus.isRecording()) return;
  if (mus.isPlaying()) {
    document.getElementById("play").innerHTML = "Play";
    document.getElementById("status").innerHTML = "Stand by";
    mus.pause();
  } else {
    document.getElementById("play").innerHTML = "Pause";
    document.getElementById("status").innerHTML = "Playing";

    // Get recorded data from database.
    $.ajax({
      url: "{% url 'mouse:get_record' %}",
      data: {"id": record_id},
      dataType: 'json',
      success: function(data) {
        if (data.success) {
          mus.setData(data.data);
          document.getElementById("ua_string").innerHTML = data.ua_string;
          mus.play(function() {
            document.getElementById("play").innerHTML = "Play";
            document.getElementById("status").innerHTML = "Stand by";
          });
          console.log(data.data);
        } else {
          console.log("{% url 'mouse:get_record' %} failed.");
        }
      },
      error: function(rs, e) {
        console.log("Failed to reach {% url 'mouse:get_record' %}.");
      }
    });
  }
};

var setSpeed = function(speed) {
  mus.setPlaybackSpeed(speed);
  if (speed == mus.speed.SLOW) {
    document.getElementById("speed").innerHTML = "Slow";
  } else if (speed == mus.speed.NORMAL) {
    document.getElementById("speed").innerHTML = "Normal";
  } else {
    document.getElementById("speed").innerHTML = "Fast";
  }
};

$(function() {
  $('#playback_form').on('submit', function(e) {
    e.preventDefault();
    var record_id = $("#playback_form #record_id :selected").text();
    play(record_id);
  });
});
