(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGraphicController', gathererGraphicController);

  function gathererGraphicController($scope, $rootScope, $http) {
    console.log('Initialize Graphic Controller');

    //$scope.$watch("$scope.emailAddress", function(){
    //    $scope.emailAddress = 'dario@gmail.com';
    //    console.log("Cambie la variable");
    //});

  }

})();
