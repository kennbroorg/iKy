(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererController', gathererController);

  /** @ngInject */
  function gathererController($scope, $rootScope, $http, $timeout) {
    $scope.emailAddress = '';
    console.log('Initialize Controller');
    console.log($scope);
     
    $scope.showInfo = function (address) {

        // The $scope is driving me crazy
        // Verify Adress
        $scope.emailAddress = address;

        // Example : Data changes
        $http.get('http://echo.jsontest.com/key/value/one/two').then(function(response) {
            $scope.restinfo = response.data;
        });

        console.log($scope);

        $timeout(function() {
          $http.get('http://echo.jsontest.com/key/value/three/four').then(function(response) {
            $scope.restinfo = response.data;
          });
        }, 2000);

        $timeout(function() {
          $http.get('http://echo.jsontest.com/key/value/puta/loca').then(function(response) {
            $scope.restinfo = response.data;
          });
        }, 5000);

        console.log($scope);


        //////////////////////////////////////////////////
        // GitHub data
        //////////////////////////////////////////////////
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
        console.log("Execute Github");
        $http({
            method: 'POST',
            url: 'http://127.0.0.1:5000/github',
            data: $.param({
                //username: $scope.emailAddress,
                username: 'kennbro',
            }),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function (data, status, headers, config) {
            $scope.github_info = data;
            console.log("Receiving... Github");
            console.log($scope);
        }).error(function (data, status, headers, config) {
            // handle error things
        });
        

        //////////////////////////////////////////////////
        // Gitlab data
        //////////////////////////////////////////////////
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
        console.log("Execute Gitlab");
        $http({
            method: 'POST',
            url: 'http://127.0.0.1:5000/gitlab',
            data: $.param({
                //username: $scope.emailAddress,
                username: 'kennbro',
            }),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function (data, status, headers, config) {
            $scope.gitlab_info = data;
            console.log("Receiving... Gitlab");
            console.log($scope);
        }).error(function (data, status, headers, config) {
            // handle error things
        });
        

        //////////////////////////////////////////////////
        // Keybase data
        //////////////////////////////////////////////////
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
        console.log("Execute Keybase");
        $http({
            method: 'POST',
            url: 'http://127.0.0.1:5000/keybase',
            data: $.param({
                //username: $scope.emailAddress,
                username: 'kennbro',
            }),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function (data, status, headers, config) {
            $scope.keybase_info = data;
            console.log("Receiving... Keybase");
            console.log($scope);
        }).error(function (data, status, headers, config) {
            // handle error things
        });
        

        //////////////////////////////////////////////////
        // Username data
        //////////////////////////////////////////////////
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
        console.log("Execute Username");
        $http({
            method: 'POST',
            url: 'http://127.0.0.1:5000/username',
            data: $.param({
                //username: $scope.emailAddress,
                username: 'kennbro',
            }),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function (data, status, headers, config) {
            $scope.username_info = data;
            console.log("Receiving... Username");
            console.log($scope);
        }).error(function (data, status, headers, config) {
            // handle error things
        });
        

    }

  }

})();
