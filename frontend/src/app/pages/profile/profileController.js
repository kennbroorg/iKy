/**
 * @author v.lugovsky
 * created on 16.12.2015
 */
(function () {
  'use strict';

  angular.module('BlurAdmin.pages.profile')
    .controller('profileController', profileController);

  /** @ngInject */
  function profileController($scope, fileReader, $filter, $uibModal, localStorageService) {

    console.log('Initialize Controller Profile');
    $scope.picture = $filter('appImage')('theme/no-photo.png');
     
    // Do something if not
    if(localStorageService.isSupported) {
        console.log("localStorage Supported");
    }

    // Control storage
    if (localStorageService.get('profile')) {
        $scope.profile = localStorageService.get('profile');

        // By now only github for profile
        console.log("Profile Controller ", $scope.profile);
        
        if ($scope.profile.github) {
            for (var items in $scope.profile.github) {
                if ($scope.profile.github[items].name != null) {
                    $scope.name = $scope.profile.github[items].name
                }
                if ($scope.profile.github[items].location != null) {
                    $scope.location = $scope.profile.github[items].location
                }
                if ($scope.profile.github[items].company) {
                    $scope.organization = $scope.profile.github[items].company
                }
                if ($scope.profile.github[items].avatar) {
                    $scope.picture = $scope.profile.github[items].avatar
                }

            }
        }

    } else {
        $scope.picture = $filter('appImage')('theme/no-photo.png');
        delete $scope.location
        delete $scope.name
        delete $scope.organization
    }

    console.log("Picture ", $scope.picture);

    // TODO : In the profile I think that a graph of relationships without circles, 
    // like a tag cloud with the service as a central node would be beautifull

    $scope.socialProfiles = [
      {
        name: 'Facebook',
        href: 'https://www.facebook.com/akveo/',
        icon: 'socicon-facebook'
      },
      {
        name: 'Twitter',
        href: 'https://twitter.com/akveo_inc',
        icon: 'socicon-twitter'
      },
      {
        name: 'Google',
        icon: 'socicon-google'
      },
      {
        name: 'LinkedIn',
        href: 'https://www.linkedin.com/company/akveo',
        icon: 'socicon-linkedin'
      },
      {
        name: 'GitHub',
        href: 'https://github.com/akveo',
        icon: 'socicon-github'
      },
      {
        name: 'StackOverflow',
        icon: 'socicon-stackoverflow'
      },
      {
        name: 'Dribbble',
        icon: 'socicon-dribble'
      },
      {
        name: 'Behance',
        icon: 'socicon-behace'
      }
    ];

    $scope.unconnect = function (item) {
      item.href = undefined;
    };

    $scope.switches = [true, true, false, true, true, false];
  }

})();
