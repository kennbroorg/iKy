/**
 * @author v.lugovksy
 * created on 16.12.2015
 */
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
