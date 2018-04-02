(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererGithubController', gathererGithubController);

  function gathererGithubController($scope, $rootScope, $http) {
    console.log('Initialize Github Controller');
  }

})();
