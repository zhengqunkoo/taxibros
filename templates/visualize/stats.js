var MS_PER_SECOND = 1000;

function genLocHandleData(path_time, path_dist, total_dist, number, best_road, best_road_coords) {
  /**
   * Show stats.
   * Dynamically create HTML stats-table, then call appearStats().
   * @return: undefined.
   */
  // Load stats
  if (number != 0) { //Gets around zero division error
    document.getElementById('average_dist').innerHTML = Math.trunc(total_dist/number) + "m";
  }
  document.getElementById('num').innerHTML = number;

  //Add, modify, or delete data depending on condition
  if ($('#a').length == 0) {
      $('#stats-table tr:last').after('<tr id = "a"><th>Better Waiting Location</th></tr>');
      $('#stats-table tr:last').after('<tr id = "b"><td>Time to travel</td><td id = "path-time">"-"</td></tr>');
      $('#stats-table tr:last').after('<tr id = "c"><td>Distance of travel</td><td id = "path-dist">"-"</td></tr>');
  }
  if (path_time==null) {
      $('#a').remove();
      $('#b').remove();
      $('#c').remove();
  } else {
      $('#path-time').html(path_time + "s");
      $('#path-dist').html(path_dist + "m");
  }
  {% if not mobile %}
  appearStats();
  {% endif %}
}

function displayTaxiStats(display_duration, display_distance) {
    //Add, modify, or delete data depending on condition
    if ($('#d').length == 0) {
        $('#stats-table tr:last').after('<tr id = "d"><th>Taxi Route Information</th></tr>');
        $('#stats-table tr:last').after('<tr id = "e"><td>Time of travel</td><td id = "taxi-time">"-"</td></tr>');
        $('#stats-table tr:last').after('<tr id = "f"><td>Distance of travel</td><td id = "taxi-dist">"-"</td></tr>');

    }
    if (display_duration==null) {
        $('#d').remove();
        $('#e').remove();
        $('#f').remove();
    } else {
        $('#taxi-time').html(display_duration);
        $('#taxi-dist').html(display_distance);
    }
}

function calcRoute(origin, destination, tr) {
    var request = {
        origin: origin,
        destination: destination,
        travelMode: 'DRIVING',
        drivingOptions: {
            departureTime: new Date(Date.now()),  // for the time N milliseconds from now.
            trafficModel: 'bestguess'
        }
    };
    directionsService.route(request, function(result, status) {
    if (status == 'OK') {
        var display_duration = null;
        var duration = null;
        var waiting_duration = 0;
        var display_distance;
        var distance;
        directionsDisplay.setDirections(result);
        directionsDisplay.setMap(map);
        tr.children('td:nth-child(19)').find('.hide').html(result.routes[0].overview_polyline);
        if (result.routes[0].legs[0].hasOwnProperty("duration_in_traffic")) {
            //Duration in traffic is only displayed when there is enough traffic
            display_duration = result.routes[0].legs[0].duration_in_traffic["text"]
            duration = result.routes[0].legs[0].duration_in_traffic["value"];
            var raw_duration = result.routes[0].legs[0].duration["value"];

        } else {
            display_duration = result.routes[0].legs[0].duration["text"]
            duration = result.routes[0].legs[0].duration["value"];
        }
        waiting_duration = 0.2*duration;
        if (raw_duration > duration) {
            waiting_duration = 0.1 * duration;
        }

        display_distance = result.routes[0].legs[0].distance["text"];
        distance = result.routes[0].legs[0].distance["value"]
        calcCost(waiting_duration, distance);
        displayTaxiStats(display_duration, display_distance);
        updateDatetimepicker(duration, tr);
        {% if not mobile %}
        appearStats();
        {% endif %}
    } else {
      window.alert('Directions request failed due to ' + status);
    }

  });
}

function calcCost(waiting_time, distance) {

    $.ajax({
      url: "{% url 'visualize:cost' %}",
      data: {
        time: waiting_time,
        distance: distance,
      },
      dataType: 'json',
      success: function(data) {

            var costs = data.cost;
            displayCosts(costs);

        },
        error: function(rs, e) {
          console.log("Failed to reach {% url 'visualize:cost' %}.");
        }
    });
}

function displayCosts(costs) {
    //Add, modify, or delete data depending on condition
    if ($('#g').length == 0) {
        $('#stats-table tr:last').after('<tr id = "g"><td>Cost of travel(low)</td><td id = "taxi-cost-l">"-"</td></tr>');
        $('#stats-table tr:last').after('<tr id = "h"><td>Cost of travel(high)</td><td id = "taxi-cost-h">"-"</td></tr>');
    }
    if (costs==null) {
        $('#g').remove();
        $('#h').remove();
    } else {
        $('#taxi-cost-l').html("$" + parseFloat(costs[0]/100).toFixed(2));
        $('#taxi-cost-h').html("$" + parseFloat(costs[1]/100).toFixed(2));
    }
}

function updateDatetimepicker(duration, tr) {
  /**
   * Update most unused datetimepicker (either pickup, or arrival).
   * Assume user does not value most unused datetimepicker.
   * If no last recently used datetimepicker, do nothing.
   * Else if get datetime is null, do nothing.
   * Else,
   *   If pickup last recently used,
   *     get pickup datetime,
   *     add duration,
   *     set arrival datetime and innerText.
   *   If arrival last recently used,
   *     get arrival datetime,
   *     minus duration,
   *     set pickup datetime and innerText.
   *   Update table.
   */
  if (lastDatetimepickerId) {
    var pickupDatetimepicker = tr.children('td:nth-child(2)').find('input');
    var arrivalDatetimepicker = tr.children('td:nth-child(4)').find('input');
    duration = duration * MS_PER_SECOND;

    if (lastDatetimepickerId == pickupDatetimepicker.attr('id')) {
      var pickupDate = pickupDatetimepicker.data('DateTimePicker').date();
      if (pickupDate) {
        var arrivalDate = new Date(pickupDate.toDate().getTime() + duration);
        arrivalDatetimepicker.datetimepicker('date', arrivalDate);
        arrivalDatetimepicker = arrivalDatetimepicker[0];
        arrivalDatetimepicker.innerText = moment(arrivalDate).format('YYYY/MM/DD HH:mm:ss');
        updateTable();
      }
    } else {
      var arrivalDate = arrivalDatetimepicker.data('DateTimePicker').date();
      if (arrivalDate) {
        var pickupDate = new Date(arrivalDate.toDate().getTime() - duration);
        pickupDatetimepicker.datetimepicker('date', pickupDate);
        pickupDatetimepicker = pickupDatetimepicker[0];
        pickupDatetimepicker.innerText = moment(pickupDate).format('YYYY/MM/DD HH:mm:ss');
        updateTable();
      }
    }
  }
}
