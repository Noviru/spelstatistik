
$(document).ready(function () {
    $.ajax({
        type: "POST",
        url: "/chartData",     //PATH
        success: function (responseData) {  //KÖR VID SUCCESS
            let match = JSON.parse(responseData);
            var wins = 0;
            var losses = 0;
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            for (var i = 0; i < match.length; i++){
                if (match[i] == 1) {
                    wins++;
                }
                else{
                  losses++;
                }
            }
              function drawChart() {
                var data = google.visualization.arrayToDataTable([
                ['Task', 'Hours per Day'],
                ['Wins', wins],
                ['Losses', losses]
              ]);
                // Optional; add a title and set the width and height of the chart
                var options = {'width':550, 'height':400, 'left':0, 'top':0, 'backgroundColor': 'transparent'};

        // Display the chart inside the <div> element with id="piechart"
                var chart = new google.visualization.PieChart(document.getElementById('piechart'));
                chart.draw(data, options);
            }

      }
    });
  });


