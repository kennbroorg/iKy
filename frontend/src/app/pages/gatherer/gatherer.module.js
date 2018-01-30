(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer', [])
      .config(routeConfig);

  /** @ngInject */
  function routeConfig($stateProvider) {
    $stateProvider
        .state('gatherer', {
          url: '/gatherer',
          templateUrl: 'app/pages/gatherer/gatherer.html',
          controller: 'gathererController',
          title: 'Gatherer',
          sidebarMeta: {
            icon: 'ion-ios-eye',
            order: 1,
          },
        });
  }

})();
