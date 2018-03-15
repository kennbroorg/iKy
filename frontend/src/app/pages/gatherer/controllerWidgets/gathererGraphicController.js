(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGraphicController', gathererGraphicController);

  function gathererGraphicController($scope, $rootScope) {
    console.log('Initialize Graphic Controller');

    $scope.allCohortsNorm = [
        {
            "cohortName": "Boston Public Schools",
            "value": 0.3337727272727273
        },
        {
            "cohortName": "Stanley Middle School",
            "value": 0.2844818181818182
        },
        {
            "cohortName": "My Students",
            "value": 0.1590909090909091
        }
    ]

  }

})();
