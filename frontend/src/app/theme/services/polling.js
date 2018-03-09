/**
 * Created by bilal on 5/1/15.
 */

(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
        .factory('$polling', pollingService);

    /** @ngInject */
    function pollingService($http) {

        var defaultPollingTime = 10000;
        var polls = [];

        return {
            startPolling: function (name, url, pollingTime, callback) {

                if(!polls[name]) {
                    var poller = function () {
                        return $http.get(url).then(function (response) {
                            callback(response);
                        });
                    }
                }
                //poller();
                polls[name] = setInterval(poller, pollingTime || defaultPollingTime);

            },

            stopPolling: function (name) {
                clearInterval(polls[name]);
                delete polls[name];
            }
        }
    };

}());
