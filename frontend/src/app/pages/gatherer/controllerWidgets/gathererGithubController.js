(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGithubController', gathererGithubController);

  function gathererGithubController($scope, $rootScope, $http) {
    console.log('Initialize Github Controller');

    //$scope.$watch("$scope.emailAddress", function(){
    //    $scope.emailAddress = 'dario@gmail.com';
    //    console.log("Cambie la variable");
    //});
    var githubData = $scope.gather.github.gather;
    console.log('githubData', githubData);

  }

})();
