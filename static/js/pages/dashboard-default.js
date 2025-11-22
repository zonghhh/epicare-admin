'use strict';
document.addEventListener('DOMContentLoaded', function () {
  setTimeout(function () {
    floatchart();
  }, 500);
});

'use strict';

// Define floatchart function
function floatchart() {
  fetch('/pageview-data')
    .then(response => response.json())
    .then(data => {
      var options = {
        chart: {
          height: 450,
          type: 'area',
          toolbar: { show: false }
        },
        dataLabels: { enabled: false },
        colors: ['#1890ff', '#13c2c2', '#f44336'],
        series: [
          { name: 'Admin', data: data.Admin },
          { name: 'Caretaker', data: data.Caretaker },
          { name: 'PWID', data: data.PWID }
        ],
        stroke: { curve: 'smooth', width: 2 },
        xaxis: { categories: data.hours }
      };

      var chartContainer = document.querySelector('#visitor-chart');
      chartContainer.innerHTML = '';
      var chart = new ApexCharts(chartContainer, options);
      chart.render();
    })
    .catch(err => {
      console.error('Failed to load pageview data:', err);
    });
}


function usercountChart(){
  fetch('/usercount-data')
    .then(response => response.json())
    .then(data => {
      var options = {
        chart: { type: 'bar', height: 365, toolbar: { show: false } },
        colors: ['#13c2c2', '#F28E2B'],
        plotOptions: { bar: { columnWidth: '45%', borderRadius: 4, distributed: true}},
        dataLabels: { enabled: false },
        series: [{
          name: 'User Count',
          data: [data.PWID, data.Caretaker] // counts from backend
        }],
        stroke: { curve: 'smooth', width: 2 },
        xaxis: {
          categories: ['PWID', 'Caretaker'], // x-axis labels
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: { show: false},
        grid: { show: false }
      };

      var el = document.querySelector('#usercount-compare');
      if (!el) return;
      el.innerHTML = '';
      var chart = new ApexCharts(el, options);
      chart.render();    
    })
    .catch(err => {
      console.error('Failed to load user count data:', err);
    });
}

// Wait for DOM loaded then run floatchart + render other charts
document.addEventListener('DOMContentLoaded', function () {
  floatchart();
  usercountChart()
});
