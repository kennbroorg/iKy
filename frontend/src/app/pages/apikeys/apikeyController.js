/**
 * @author v.lugovksy
 * created on 16.12.2015
 */
(function () {
  'use strict';

  angular.module('BlurAdmin.pages.timeline')
      .controller('apikeyController', apikeyController);

  /** @ngInject */
  function apikeyController($scope, $http, editableOptions, editableThemes) {

    console.log('Initialize Controller API Key');

    $http.post('http://127.0.0.1:5000/apikey')
        .success(function (data, status, headers, config) {
            console.log("Receiving... ApiKeys");
            $scope.keys = data.keys;
            console.log("Keys ", $scope.keys);
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
      console.log("UPDATE", $scope.keys);

      $http.post('http://127.0.0.1:5000/apikey', $scope.keys);

      // var r_keys = $http({
      //         method: 'POST',
      //         url: 'http://127.0.0.1:5000/apikey',
      //         data: $.param({
      //             apikeys: $scope.keys,
      //         }),
      //         headers: {'Content-Type': 'application/json'}
      //     }).success(function (data, status, headers, config) {
      //         console.log("Sending... ApiKeys");
      //         $scope.keys = data.keys;
      //         console.log("Keys ", $scope.keys);
      //     }).error(function (data, status, headers, config) {
      //         // handle error things
      //     });

    };

    editableOptions.theme = 'bs3';
    editableThemes['bs3'].submitTpl = '<button type="submit" class="btn btn-primary btn-with-icon"><i class="ion-checkmark-round"></i></button>';
    editableThemes['bs3'].cancelTpl = '<button type="button" ng-click="$form.$cancel()" class="btn btn-default btn-with-icon"><i class="ion-close-round"></i></button>';

  }
})();
