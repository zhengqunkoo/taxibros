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

           var parseTime = d3.timeParse("%s");
           day_stats.forEach(function(d) { d.count = d.count; d.timestamp = parseTime(d.timestamp); return d;});


           var y = d3.scaleLinear()
               .domain(d3.extent(day_stats, function(d) {return d.count;}))
               .range([height,0]);
           var yAxis = d3.axisLeft(y)
               .scale(y)
               .ticks(5, "s");



           var x = d3.scaleTime().domain(d3.extent(day_stats, function(d) {return d.timestamp;})).range([0,width]);
           var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%I:00 %p")).tickArguments(d3.timeHour.every(1));



           var rect = chart.selectAll("g")
               .data(day_stats)
             .enter().append("rect")
               .attr("transform", function(d, i) { return "translate(" + (margin.left + (i * barWidth)) + ",0)"; })
               .attr("y", height) //To initialize bar outside chart
               .attr("width", barWidth - 1)
               .attr("height", function(d) {return height-y(d.count);});

           rect.transition()
               .delay(function(d, i) {return i * 100; })
               .attr("y",function(d) {return y(d.count);});


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
