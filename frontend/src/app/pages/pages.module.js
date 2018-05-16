(function () {
  'use strict';

  angular.module('BlurAdmin.pages', [
    'ui.router',
    'BlurAdmin.pages.profile',
    'BlurAdmin.pages.gatherer',
    'BlurAdmin.pages.dashiky',
    'BlurAdmin.pages.timeline',
    'BlurAdmin.pages.apikeys',
  ])
      .config(routeConfig);

  /** @ngInject */
  function routeConfig($urlRouterProvider, baSidebarServiceProvider) {
    $urlRouterProvider.otherwise('/dashiky');
  }

})();
