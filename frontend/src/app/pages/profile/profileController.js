(function () {
  'use strict';

  angular.module('BlurAdmin.pages.profile')
    .controller('profileController', profileController);

  /** @ngInject */
  function profileController($scope, fileReader, $filter, $uibModal, localStorageService) {

    console.log('Initialize Controller Profile');
    $scope.picture = $filter('appImage')('theme/no-photo.png');
     
    function isSocial(name) {
        for(var i=0; i<=$scope.smartProfile.social.length; i++) {
            if ($scope.smartProfile.social[i] != undefined && $scope.smartProfile.social[i]['name'] == name) return true;
        }
        return false;
    }
    function isPhotos(photo) {
        for(var i=0; i<=$scope.smartProfile.photos.length; i++) {
            if ($scope.smartProfile.photos[i] != undefined && $scope.smartProfile.photos[i]['picture'] == photo['picture']) return i;
        }
        return -1;
    }

    // Do something if not
    if(localStorageService.isSupported) {
        console.log("localStorage Supported");
    }

    // Control storage
    if (localStorageService.get('profile')) {
        $scope.profile = localStorageService.get('profile');

        // By now only github for profile
        console.log("Profile Controller ", $scope.profile, $scope.smartProfile);
        $scope.smartProfile = new Object;
        

        if ($scope.profile.fullcontact) {
            for (var items in $scope.profile.fullcontact) {
                if ($scope.profile.fullcontact[items].name != null) {
                    $scope.smartProfile.name = $scope.profile.fullcontact[items].name
                }
                if ($scope.profile.fullcontact[items].location != null) {
                    $scope.smartProfile.location = $scope.profile.fullcontact[items].location
                }
                if ($scope.profile.fullcontact[items].gender != null) {
                    $scope.smartProfile.gender = $scope.profile.fullcontact[items].gender
                }
                // if ($scope.profile.fullcontact[items].organization) {
                //     $scope.organization = $scope.profile.github[items].company
                // }
                // if ($scope.profile.fullcontact[items].photos) {
                //     $scope.picture = $scope.profile.github[items].avatar
                // }

            }
        }

        // Social Profile
        $scope.smartProfile.social = [];
        for (var module in $scope.profile) {
            for (var social in $scope.profile[module]) {
                if ('social' in $scope.profile[module][social]) {
                    for(var i=0; i<$scope.profile[module][social]['social'].length; i++) {
                        if (isSocial($scope.profile[module][social]['social'][i]['name']) != true) {
                            $scope.profile[module][social]['social'][i]['icon'] = 'socicon-' + $scope.profile[module][social]['social'][i]['name']
                            $scope.smartProfile.social.push($scope.profile[module][social]['social'][i]);
                        }
                    }

                }
            }
        }

        // Photo Profile
        $scope.smartProfile.photos = [];
        for (var module in $scope.profile) {
            for (var photos in $scope.profile[module]) {
                if ('photos' in $scope.profile[module][photos]) {
                    for(var i=0; i<$scope.profile[module][photos]['photos'].length; i++) {
                        var isPhotoResult = isPhotos($scope.profile[module][photos]['photos'][i]['picture']);
                        if (isPhotoResult == -1) {
                            $scope.smartProfile.photos.push($scope.profile[module][photos]['photos'][i]);
                        } else {
                            $scope.smartProfile.photos[isPhotoResult]['title'] = $scope.smartProfile.photos[isPhotoResult]['title'] + 
                                ' - ' + $scope.profile[module][photos]['photos'][i]['title'];
                        }
                    }
                }
            }
        }

    } else {
        $scope.picture = $filter('appImage')('theme/no-photo.png');
        delete $scope.location
        delete $scope.name
        delete $scope.organization
    }

    // TODO : In the profile I think that a graph of relationships without circles, 
    // like a tag cloud with the service as a central node would be beautifull


    console.log("smartProfile", $scope.smartProfile);

    $scope.unconnect = function (item) {
      item.href = undefined;
    };

    $scope.switches = [true, true, false, true, true, false];
  }

})();
