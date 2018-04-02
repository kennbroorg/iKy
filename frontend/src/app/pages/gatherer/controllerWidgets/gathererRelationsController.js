(function () {
  'use strict';

  angular.module('BlurAdmin.pages.gatherer')
    .controller('gathererRelationsController', gathererRelationsController);

  function gathererRelationsController($scope, $rootScope) {
    console.log('Initialize Relations Controller');

    $scope.relationsNode = [
        {
            "name-node": "Github",
            "title": "Github",
            "subtitle": "",
            // "icon": "\uf113",
            "icon": "\uf09b",
            "link": "Github"
        },
        {
            "name-node": "ReposGit",
            "title": "Repos",
            "subtitle": "7",
            "icon": "\uf07c",
            "link": "Github"
        },
        {
            "name-node": "FollowersGit",
            "title": "Followers",
            "subtitle": "12",
            "icon": "\uf0c0",
            "link": "Github"
        },
        {
            "name-node": "followingGit",
            "title": "Following",
            "subtitle": "2",
            "icon": "\uf0c0",
            "link": "Github"
        },
        {
            "name-node": "nameGit",
            "title": "Git Name",
            "subtitle": "Juan Pablo Daniel Borgna",
            "icon": "\uf007",
            "link": "Github"
        }
    ]

  }

})();
