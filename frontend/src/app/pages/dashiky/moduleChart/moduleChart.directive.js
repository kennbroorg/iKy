(function () {
  'use strict';

  angular.module('BlurAdmin.pages.dashiky')
      .directive('moduleChart', moduleChart);

  /** @ngInject */
  function moduleChart() {
    return {
      restrict: 'E',
      controller: 'moduleChartController',
      templateUrl: 'app/pages/dashiky/moduleChart/moduleChart.html'
    };
  }
})();
