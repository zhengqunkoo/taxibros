function drawChart() {

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

           // Typical action to be performed when the document is ready:
           var response = JSON.parse(this.responseText);
           var day_stats = response.day_stats;
           var title = response.chart_title;
           var height = 210,
               width = 300;
           var margin = {top: 20, right: 10, bottom: 30, left: 40};

           var chart = d3.select(".chart")
               .attr("height", height);
           chart.attr("width", width);

           height = height - margin.top - margin.bottom;
           width = width - margin.left - margin.right;
           var barWidth = width/day_stats.length;

           var y = d3.scaleLinear()
               .domain([0, d3.max(day_stats)])
               .range([height,0]);
           var yAxis = d3.axisLeft(y)
               .scale(y)
               .ticks(5, "s");

           var parseTime = d3.timeParse("%I:%M %p");
           var startTime = parseTime("06:00 AM");
           var endTime = parseTime("05:00 AM");

           var x = d3.scaleTime().domain([startTime, endTime]).range([0,width]);
           var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%I:%M %p")).tickArguments(d3.timeMinute.every(60));



           var rect = chart.selectAll("g")
               .data(day_stats)
             .enter().append("rect")
               .attr("transform", function(d, i) { return "translate(" + (margin.left + (i * barWidth)) + ",0)"; })
               .attr("y", height) //To initialize bar outside chart
               .attr("width", barWidth - 1)
               .attr("height", function(d) {return height-y(d);});

           rect.transition()
               .delay(function(d, i) {return i * 100; })
               .attr("y",function(d) {return y(d);});


           chart.append("g")
               .attr("transform", "translate(" + margin.left+ ",0)")
               .call(yAxis);
           chart.append("g")
                .attr("transform", "translate(" + margin.left + "," + height + ")")
              .call(xAxis)
              .selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");

            $("#chart-title").text(title);
        }
    };
    xhttp.open("GET", "{% url 'visualize:genChart' %}", true);
    xhttp.send();
}

function removeStats() {
    //Function for container stats to disappear to the side
  $('#container-stats').stop().animate({right: "-50%"},1200);
}

function appearStats() {
  $('#container-stats').stop().animate({right: "0%"},400);
}
