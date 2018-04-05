(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererPhotosController', gathererPhotosController);

  function gathererPhotosController($scope, $rootScope, $http) {
    console.log('Initialize Photos Controller');
  }

})();
