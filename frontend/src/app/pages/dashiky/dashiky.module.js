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
          title: 'Home',
          sidebarMeta: {
            icon: 'ion-android-home',
            order: 0,
          },
        });
  }

})();
