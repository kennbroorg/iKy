/**
 * @author v.lugovsky
 * created on 16.12.2015
 */
(function () {
  'use strict';

  angular.module('BlurAdmin.pages.dashiky', [])
      .config(routeConfig);

  /** @ngInject */
  function routeConfig($stateProvider) {
    $stateProvider
        .state('dashiky', {
          url: '/dashiky',
          templateUrl: 'app/pages/dashiky/dashiky.html',
          title: 'Dashiky',
          sidebarMeta: {
            icon: 'ion-stats-bars',
            order: 0,
          },
        });
  }

})();
