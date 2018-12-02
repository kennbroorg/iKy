(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('githubCalendar', githubCalendar);

  function githubCalendar($scope, $rootScope, $http) {
    console.log('Initialize Github Calendar Controller');

    // $scope.$watch('gather.github.result[4].graphic[1].cal_actual', function(texts) {
    //     $scope.gather.github.result[3].graphic[1].cal_actual = texts.replace(/ebedf0/g, "666666");
    // });
    // $scope.$watch('gather.github.result[4].graphic[2].cal_previous', function(texts) {
    //     $scope.gather.github.result[3].graphic[2].cal_previous = texts.replace(/ebedf0/g, "666666");
    // });
  }

})();
