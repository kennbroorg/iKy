/**
 * @author a.demeshko
 * created on 1/12/16
 */
(function () {
  'use strict';

  angular.module('BlurAdmin.pages.apikeys', [])
    .config(routeConfig);

  /** @ngInject */
  function routeConfig($stateProvider) {
    $stateProvider
      .state('apikey', {
        url: '/apikey',
        templateUrl: 'app/pages/apikeys/apikey.html',
        controller: 'apikeyController',
        title: 'API Keys',
        sidebarMeta: {
          icon: 'ion-gear-a',
          order: 5,
        },
      });
  }
})();
