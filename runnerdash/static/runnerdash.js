window.chartColors = {
	red: 'rgb(255, 99, 132)',
	orange: 'rgb(255, 159, 64)',
	yellow: 'rgb(255, 205, 86)',
	green: 'rgb(75, 192, 192)',
	blue: 'rgb(54, 162, 235)',
	purple: 'rgb(153, 102, 255)',
	grey: 'rgb(201, 203, 207)'
};

// speed dashboard
function speedDashboard(timestamps, speeds) {
    var data = {
    labels : timestamps,
    datasets : [
        {
          label: 'speed',
          backgroundColor: window.chartColors.blue,
          borderColor: window.chartColors.blue,
          fill: false,
          data : speeds
        }]
    };
  
    Chart.defaults.global.animationSteps = 50;
    Chart.defaults.global.tooltipYPadding = 16;
    Chart.defaults.global.tooltipCornerRadius = 0;
    Chart.defaults.global.tooltipTitleFontStyle = "normal";
    Chart.defaults.global.tooltipFillColor = "rgba(0,0,0,0.8)";
    Chart.defaults.global.animationEasing = "easeOutBounce";
    Chart.defaults.global.responsive = false;
    Chart.defaults.global.scaleLineColor = "black";
    Chart.defaults.global.scaleFontSize = 16;
  
    // get bar chart canvas
    var speed_chart = document.getElementById("speed-chart").getContext("2d");
  
    steps = 10;
    max = 10;
    // draw bar chart
    var SpeedChart = new Chart(speed_chart, {
      type: "line",
        data: data,
        options: {
          title: 'speed',
          scales: {
            xAxes: [{
              scaleLabel: {
                display: true,
                labelString: 'time'
              }
            }],
            yAxes: [{
              scaleLabel: {
                display: true,
                labelString: 'km/h'
              }
            }]
          }, 
          tooltips: {
            mode: 'index',
            intersect: false,
          },
          hover: {
            mode: 'nearest',
            intersect: true
          },
          responsive: true,
          maintainAspectRatio: false
        }
    });
}

$(document).ready(function($) {
  $(".clickable-row").click(function() {
    $("#activity-id").val($(this).data("activity"));
    $("#activity-form").submit();
  });

  $("#wizard-modal").modal({
    backdrop: 'static',
    keysboard: false
  });

  $('#wizard-form').on('submit', function(e){
    e.preventDefault();
    $(this).validate();
    if ($(this).valid()) {
      $.ajax({
        url: "wizard",
        type: "POST",
        data: $(this).serialize(),
        success: function(data){
          $('#wizard-modal').modal('hide');    
          window.location = data;
        },
        error: function(jqXHR, status, error) {
          console.log(status + ": " + error);
        }
      });
    }
  });

  $("#wizard-submit").on('click', function() {
      $("#wizard-form").submit();
  });
});

