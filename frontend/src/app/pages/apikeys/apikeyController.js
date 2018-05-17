(function () {
  'use strict';

  angular.module('BlurAdmin.pages.timeline')
      .controller('apikeyController', apikeyController);

  /** @ngInject */
  function apikeyController($scope, $http, editableOptions, editableThemes, toastr, toastrConfig) {
    console.log('Initialize Controller API Key');

    // Notifications
    var defaultConfig = angular.copy(toastrConfig);
    var openedToasts = [];
    $scope.options = {
      autoDismiss: false,
      positionClass: 'toast-top-right',
      type: 'info',
      timeOut: '1500',
      extendedTimeOut: '2000',
      allowHtml: false,
      closeButton: false,
      tapToDismiss: true,
      progressBar: false,
      newestOnTop: false,
      maxOpened: 0,
      preventDuplicates: false,
      preventOpenDuplicates: false
    };
    angular.extend(toastrConfig, $scope.options);

    $http.post('http://127.0.0.1:5000/apikey')
        .success(function (data, status, headers, config) {
            $scope.keys = data.keys;
        })

    $scope.removeKey = function(index) {
      $scope.keys.splice(index, 1);
    };

    $scope.addKey = function() {
      $scope.inserted = {
        id: $scope.keys.length+1,
        name: '',
        status: null
      };
      $scope.keys.push($scope.inserted);
    };

    $scope.updateKey = function() {
        openedToasts.push(toastr['success']("The keys have been stored", "Save Keys"));
        $http.post('http://127.0.0.1:5000/apikey', $scope.keys);
    };

    editableOptions.theme = 'bs3';
    editableThemes['bs3'].submitTpl = '<button type="submit" class="btn btn-primary btn-with-icon"><i class="ion-checkmark-round"></i></button>';
    editableThemes['bs3'].cancelTpl = '<button type="button" ng-click="$form.$cancel()" class="btn btn-default btn-with-icon"><i class="ion-close-round"></i></button>';

  }
})();
