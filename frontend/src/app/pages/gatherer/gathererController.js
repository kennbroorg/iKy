(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererController', gathererController);

  /** @ngInject */
  function gathererController($scope, $rootScope, $http, $timeout, $polling, $q, localStorageService) {
    // $scope.emailAddress = '';
    $scope.tasks = new Array();
    console.log('Initialize Controller');
     
    // Do something if not
    if(localStorageService.isSupported) {
        console.log("localStorage Supported");
    }

    // Control storage
    if (localStorageService.get('button-off')) {
        $scope.button = localStorageService.get('button-off');
    }
    if (localStorageService.get('emailAddress')) {
        $scope.emailAddress = localStorageService.get('emailAddress');
    }
    if (localStorageService.get('gather')) {
        $scope.gather = localStorageService.get('gather');
    }

    $scope.clearInfo = function () {
        // Aniquilate everything
        localStorageService.remove('button-off');
        localStorageService.remove('gather');
        delete $scope.button;
        delete $scope.gather;
    }

    $scope.showInfo = function (address) {

        // Verify Adress
        $scope.emailAddress = address;
        localStorageService.set('emailAddress', address);
        $scope.username = $scope.emailAddress.split("@")[0];
        $rootScope.emailAddress = address;
        $rootScope.username = $scope.emailAddress.split("@")[0];
        $scope.button = 'OFF';
        localStorageService.set('button-off', 'OFF');


        //////////////////////////////////////////////////
        // Testing
        //////////////////////////////////////////////////
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
        console.log("Execute Testing");
        $http({
            method: 'POST',
            url: 'http://127.0.0.1:5000/testing',
            data: $.param({
                testing: 'ok',
                username: $scope.username,
            }),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }); //TODO : Use to test backend availabillity


        //////////////////////////////////////////////////
        // GitHub data
        //////////////////////////////////////////////////
        console.log("Execute Github");
        // $http({
        var r_github = $http({
                method: 'POST',
                url: 'http://127.0.0.1:5000/github',
                data: $.param({
                    username: $scope.username,
                }),
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success(function (data, status, headers, config) {
                //$scope.github_info = data;
                console.log("Receiving... Github");
                $scope.tasks.push({
                    "module" : data.module,
                    "param" : data.param,
                    "task_id" : data.task,
                    "state" : "PENDING",
                });

                //$http.get('http://127.0.0.1:5000/result/' + data.goto)
                //.success(function (data, status, headers, config) {
                //    $scope.github_info = data;
                //    console.log($scope.github_info);
                //}).error(function (data, status, headers, config) {
                //    // handle error things
                //});

            }).error(function (data, status, headers, config) {
                // handle error things
            });
        

        //////////////////////////////////////////////////
        // Gitlab data
        //////////////////////////////////////////////////
        console.log("Execute Gitlab");
        //$http({
        var r_gitlab = $http({
                method: 'POST',
                url: 'http://127.0.0.1:5000/gitlab',
                data: $.param({
                    username: $scope.username,
                }),
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success(function (data, status, headers, config) {
                console.log("Receiving... Gitlab");
                $scope.tasks.push({
                    "module" : data.module,
                    "param" : data.param,
                    "task_id" : data.task,
                    "state" : "PENDING",
                });

                //$http.get('http://127.0.0.1:5000/result/' + data.goto)
                //.success(function (data, status, headers, config) {
                //    $scope.gitlab_info = data;
                //    console.log($scope.gitlab_info);
                //}).error(function (data, status, headers, config) {
                //    // handle error things
                //});

            }).error(function (data, status, headers, config) {
                // handle error things
            });
        

        //////////////////////////////////////////////////
        // Keybase data
        //////////////////////////////////////////////////
        console.log("Execute Keybase");
        //$http({
        var r_keybase = $http({
                method: 'POST',
                url: 'http://127.0.0.1:5000/keybase',
                data: $.param({
                    username: $scope.username,
                }),
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success(function (data, status, headers, config) {
                console.log("Receiving... Keybase");
                $scope.tasks.push({
                    "module" : data.module,
                    "param" : data.param,
                    "task_id" : data.task,
                    "state" : "PENDING",
                });

                //$http.get('http://127.0.0.1:5000/result/' + data.goto)
                //.success(function (data, status, headers, config) {
                //    $scope.keybase_info = data;
                //    console.log($scope.keybase_info);
                //}).error(function (data, status, headers, config) {
                //    // handle error things
                //});

            }).error(function (data, status, headers, config) {
                // handle error things
            });
        

        //////////////////////////////////////////////////
        // Usersearch data
        //////////////////////////////////////////////////
        //console.log("Execute Usersearch");
        //$http({
        //    method: 'POST',
        //    url: 'http://127.0.0.1:5000/usersearch',
        //    data: $.param({
        //        username: $scope.username,
        //    }),
        //    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        //}).success(function (data, status, headers, config) {
        //    console.log("Receiving... Usersearch");
        //    $scope.tasks.push({
        //        "module" : data.module,
        //        "param" : data.param,
        //        "task_id" : data.task,
        //        "state" : "PENDING",
        //    });
        //    

        //    $http.get('http://127.0.0.1:5000/result/' + data.goto)
        //    .success(function (data, status, headers, config) {
        //        $scope.usersearch_info = data;
        //        console.log($scope.usersearch_info);
        //    }).error(function (data, status, headers, config) {
        //        console.log(data);
        //        console.log(status);
        //        console.log(headers);
        //        console.log(config);
        //        // handle error things
        //    });

        //}).error(function (data, status, headers, config) {
        //    console.log(data);
        //    console.log(status);
        //    console.log(headers);
        //    console.log(config);
        //    // handle error things
        //});
        
        // Progress bar
        var progressTotal = 0
        var progressChunk = 0
        var progressActual = 0
        $('#progress-gather').css('width', '0%').attr('aria-valuenow', '0');

        function callbackProccessData(response) {
            // console.log("Call", response);
            if (response.data.state == "SUCCESS"){
                console.log("***************************************");
                console.log("App : ", response.data.task_app, " SUCCESS")
                $polling.stopPolling(response.data.task_app);

                $http.get('http://127.0.0.1:5000/result/' + response.data.task_id)
                .success(function (data, status, headers, config) {
                    $scope.gather[response.data.task_app] = data;
                    localStorageService.set('gather', $scope.gather);

                    console.log($scope.gather, $scope.gather.keybase);
                    progressActual = progressActual + progressChunk;
                    $('#progress-gather').css('width', progressActual+'%').attr('aria-valuenow', progressActual);
                    console.log(progressTotal, progressChunk, progressActual);

                }).error(function (data, status, headers, config) {
                    // handle error things
                });
            }
        };

        $q.all([r_github, r_gitlab, r_keybase]).then(function() {
            $scope.gather = new Object();
            var task;
            for (task in $scope.tasks) {
                console.log($scope.tasks[task].task_id, $scope.tasks[task].module)
                $polling.startPolling($scope.tasks[task].module, 'http://127.0.0.1:5000/state/' + $scope.tasks[task].task_id + '/' +  $scope.tasks[task].module, 1000, callbackProccessData);

            // Progress bar
            progressTotal = $scope.tasks.length;
            progressChunk = 100 / progressTotal;
            console.log(progressTotal, progressChunk, progressActual);
            // $('.progress-gather').css('width', valeur+'%').attr('aria-valuenow', valeur);
            //
            };
        });



    }

  }


})();
