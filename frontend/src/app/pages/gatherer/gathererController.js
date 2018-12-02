(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererController', gathererController);

  /** @ngInject */
  function gathererController($scope, $rootScope, $http, $timeout, $polling, $q, localStorageService, toastr, toastrConfig) {
    console.log('Initialize Controller');

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

    $scope.tasks = new Array();
     
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
        // $scope.gather = JSON.parse(localStorageService.get('gather'));
        // $rootScope.gather = localStorageService.get('gather');
        // $scope.gather = localStorageService.get('gather');
        console.log("Gather !!! localStorage", localStorageService.get('gather'));
        console.log("Gather !!! scope", $scope.gather);
        console.log("Gather !!! root", $rootScope.gather);
    } else {
        // $rootScope.gather = new Object();
        $scope.gather = new Object();
    }
    if ($rootScope.gather) {
        $scope.gather = $rootScope.gather;
    }
    console.log("Gather !!! root", $rootScope.gather);
    console.log("Gather !!! ", $scope.gather);

    $scope.clearInfo = function () {
        // Aniquilate everything
        for(var i=0; i<$scope.tasks.length; i++) {
            $polling.stopPolling($scope.tasks[i].module + $scope.tasks[i].task_id);
        }
        localStorageService.remove('button-off');
        localStorageService.remove('gather');
        localStorageService.remove('emailAddress');
        localStorageService.remove('timeline');
        localStorageService.remove('profile');
        localStorageService.clearAll();
        delete $scope.button;
        delete $scope.gather;
        delete $rootScope.gather;
        delete $rootScope.username;
        delete $rootScope.emailAddress;
        delete $scope.emailAddress;
        delete $scope.username;
        delete $scope.tasks;
        delete $scope.tasklist;
        delete $scope.timeline;
        delete $scope.profile;
        delete $scope.data;
        $scope.tasks = new Array();
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
        console.log("Execute Testing");
        $http.post('http://127.0.0.1:5000/testing', {testing: "ok", username: $scope.username});

        //////////////////////////////////////////////////
        // TaskList
        //////////////////////////////////////////////////
        console.log("Execute TaskList");
        $http.get('http://127.0.0.1:5000/tasklist')
            .success(function (data, status, headers, config) {
                $scope.tasklist = data.modules;
                console.log("Task List : ", $scope.tasklist);
            });

        //////////////////////////////////////////////////
        // Fullcontact data
        //////////////////////////////////////////////////
        console.log("Execute Fullcontact");
        $http.post('http://127.0.0.1:5000/fullcontact', {username: $scope.emailAddress, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "Initial Gather"));
                // KKK : Borrar
                console.log("Enciendo : ", data.module + data.task);
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);

            });

        //////////////////////////////////////////////////
        // GitHub data
        //////////////////////////////////////////////////
        console.log("Execute Github");
        $http.post('http://127.0.0.1:5000/github', {username: $scope.username, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "Github"));
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
            });

        //////////////////////////////////////////////////
        // GhostProject data
        //////////////////////////////////////////////////
        console.log("Execute GhostProject");
        $http.post('http://127.0.0.1:5000/ghostproject', {username: $scope.emailAddress, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "GhostProject"));
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
            });

        //////////////////////////////////////////////////
        // Linkedin data
        //////////////////////////////////////////////////
        console.log("Execute Linkedin");
        $http.post('http://127.0.0.1:5000/linkedin', {username: $scope.emailAddress, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "Linkedin"));
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
            });

        //////////////////////////////////////////////////
        // Keybase data
        //////////////////////////////////////////////////
        console.log("Execute Keybase");
        $http.post('http://127.0.0.1:5000/keybase', {username: $scope.username, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "Keybase"));
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
            });

        
        //////////////////////////////////////////////////
        // Leaks data
        //////////////////////////////////////////////////
        console.log("Execute Leaks");
        $http.post('http://127.0.0.1:5000/leaks', {username: $scope.emailAddress, from: 'Initial'})
            .success(function (data, status, headers, config) {
                $scope.tasks.push({
                    "module" : data.module, "param" : data.param,
                    "task_id" : data.task, "state" : "PENDING", "from" : "Initial", 
                });
                openedToasts.push(toastr['info']("", "Leaks"));
                $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
            });


        //////////////////////////////////////////////////
        // Callback 
        //////////////////////////////////////////////////
        // Progress bar
        var progressTotal = 0
        var progressChunk = 0
        var progressActual = 0
        $('#progress-gather').css('width', '0%').attr('aria-valuenow', '0');

        function isTaskImplemented(module) {
            for(var i=0; i<$scope.tasklist.length; i++) {
                if ($scope.tasklist[i] == module) return true;
            }
        }

        function isTaskRun(taskId) {
            for(var i=0; i<$scope.tasks.length; i++) {
                if ($scope.tasks[i].task_id == taskId) return i;
            }
            return -1;
        }

        function isModuleParamRun(module, param, from) {
            for(var i=0; i<$scope.tasks.length; i++) {
                if ($scope.tasks[i].module == module && $scope.tasks[i].param == param && $scope.tasks[i].from == from) return i;
            }
            return -1;
        }

        // Process data result
        function callbackProccessData(response) {
            if (response.data.state == "SUCCESS"){
                console.log("FINISH !!", response.data.task_app, response.data.task_id, response.data.state);
                openedToasts.push(toastr['success']("", response.data.task_app));
                $polling.stopPolling(response.data.task_app + response.data.task_id);
                if (isTaskRun(response.data.task_id) != -1) {
                    $scope.tasks[isTaskRun(response.data.task_id)].state = response.data.state;
                }


                $http.get('http://127.0.0.1:5000/result/' + response.data.task_id)
                .success(function (data, status, headers, config) {
                    for (var items in data.result) {

                        if (data.result[items].profile != null) {
                            if ($scope.profile == null) { $scope.profile = new Object(); }
                            $scope.profile[response.data.task_app] = data.result[items].profile;
                            console.log("Profile ", $scope.profile);
                            localStorageService.set('profile', $scope.profile);
                        }

                        if (data.result[items].timeline != null) {
                            if ($scope.timeline == null) { $scope.timeline = []; }
                                for (var i in data.result[items].timeline) {
                                    $scope.timeline.push(data.result[items].timeline[i]);
                                }
                            console.log("Timeline ", $scope.timeline);
                            localStorageService.set('timeline', $scope.timeline);
                        }

                        if (data.result[items].tasks != null) {
                            for (var run in data.result[items].tasks) {
                                if (isTaskImplemented(data.result[items].tasks[run].module) == true && 
                                    isModuleParamRun(data.result[items].tasks[run].module, data.result[items].tasks[run].param, 
                                            data.result[items].tasks[run].from) == -1) {
                                    $http.post('http://127.0.0.1:5000/' + data.result[items].tasks[run].module, {username: data.result[items].tasks[run].param, 
                                            from: response.data.task_app})
                                        .success(function (data, status, headers, config) {
                                            $scope.tasks.push({
                                                "module" : data.module, "param" : data.param,
                                                "task_id" : data.task, "state" : "PENDING", "from" : response.data.task_app,
                                            });
                                            openedToasts.push(toastr['info']("", data.module));
                                            $polling.startPolling(data.module + data.task, 'http://127.0.0.1:5000/state/' + data.task + '/' +  data.module, 1000, callbackProccessData);
                                        });
                                } else {
                                    console.log("You must implement : ", data.result[items].tasks[run].module);
                                }
                            }
                        }

                    }

                    if ($scope.gather == null) { $scope.gather = new Object(); }
                    if ($rootScope.gather == null) { $rootScope.gather = new Object(); }
                    $scope.gather[response.data.task_app] = data;
                    $rootScope.gather[response.data.task_app] = data;
                    // localStorageService.set('gather', JSON.stringify($scope.gather));
                    // localStorageService.set('gather', $scope.gather);
                    console.log('Gather', $scope.gather);
                    console.log('Gather ROOT', $rootScope.gather);
                    console.log('Task', $scope.tasks);
                   
                });
            }
        };


        // Progress Bar
        $scope.$watch('tasks', function() {
            progressTotal = $scope.tasks.length;
            progressChunk = 100 / progressTotal;
            progressActual = 0;
            for (var task in $scope.tasks) {
                if ($scope.tasks[task].state == 'SUCCESS') {
                    progressActual = progressActual + progressChunk;
                }
            }
            $('#progress-gather').css('width', progressActual+'%').attr('aria-valuenow', progressActual);
            console.log(progressTotal, progressChunk, progressActual);
        }, true);

        // Wait to task begin
        // $q.all([r_gitlab, r_keybase]).then(function() {
        //     $scope.gather = new Object();
        //     // var task;
        //     for (var task in $scope.tasks) {
        //         console.log("Task ", $scope.tasks[task].task_id, $scope.tasks[task].module)
        //         $polling.startPolling($scope.tasks[task].module, 'http://127.0.0.1:5000/state/' + $scope.tasks[task].task_id + '/' +  $scope.tasks[task].module, 1000, callbackProccessData);

        //     // Progress bar
        //     progressTotal = $scope.tasks.length;
        //     progressChunk = 100 / progressTotal;
        //     console.log(progressTotal, progressChunk, progressActual);
        //     };
        // });



    }

  }


})();
