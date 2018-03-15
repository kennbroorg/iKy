(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGraphic2Controller', gathererGraphic2Controller);

  function gathererGraphic2Controller($scope, $rootScope) {
    console.log('Initialize Graphic2 Controller');

    $scope.allCohortsNorm2 = [
        {
            "cohortName": "MIT Public Schools",
            "value": 0.5337727272727273
        },
        {
            "cohortName": "PEPPER Middle School",
            "value": 0.1844818181818182
        },
        {
            "cohortName": "My Students",
            "value": 0.4590909090909091
        }
    ]

  }

})();
