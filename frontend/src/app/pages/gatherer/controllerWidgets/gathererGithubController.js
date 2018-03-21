(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGithubController', gathererGithubController);

  function gathererGithubController($scope, $rootScope, $http) {
    console.log('Initialize Github Controller');

    var init = function () {
        // $scope.isStarted = $scope.isStarted + "Project now initialized";
        console.log('*** Mensaje despues del load view ***');
    }
    init();
    //$scope.$watch("$scope.emailAddress", function(){
    //    $scope.emailAddress = 'dario@gmail.com';
    //    console.log("Cambie la variable");
    //});
    // if ($scope.gather) {
    //     console.log('EXISTE Gather', $scope.gather);
    //     // var githubData = $scope.gather.github.gather;
    //     // console.log('githubData', githubData);
    // }
    // if ($scope.gather.github) {
    //     console.log('EXISTE Github', $scope.gather.github);
    //     // var githubData = $scope.gather.github.gather;
    //     // console.log('githubData', githubData);
    // }
    // if ($scope.gather.github.result) {
    //     console.log('githubData', $scope.gather.github.result);
    //     // var githubData = $scope.gather.github.gather;
    //     // console.log('githubData', githubData);
    // }

  }

})();
