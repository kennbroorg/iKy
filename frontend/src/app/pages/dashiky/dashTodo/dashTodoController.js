(function () {
  'use strict';

  angular.module('BlurAdmin.pages.dashiky')
      .controller('dashTodoController', dashTodoController);

  /** @ngInject */
  function dashTodoController($scope, baConfig) {

    $scope.transparent = baConfig.theme.blur;
    var dashboardColors = baConfig.colors.dashboard;
    var colors = [];
    for (var key in dashboardColors) {
      colors.push(dashboardColors[key]);
    }

    function getRandomColor() {
      var i = Math.floor(Math.random() * (colors.length - 1));
      return colors[i];
    }

    $scope.todoList = [
      { text: 'Think about running the same module with different parameters' },
      { text: 'Minor changes pending: grep -r -i TODO in the backend' },
      { text: 'Use tag input to select the modules to will run' },
      { text: 'Validation of username and email modules' },
      { text: 'Create module Klout with crawling' },
      { text: 'Manage multiples api keys' },
      { text: 'List module and submodule' },
      { text: 'Maps module running and submodule running' },
      { text: 'Convert definitions in boards' },
      { text: 'Contributors in dash, from based software and github contributions' },
      { text: 'Documentation for contributions' },
      { text: 'Normalize everything, python and angularjs' },
      { text: 'Fix : When resize the windows the logo doenst resize' },
    ];

    $scope.todoList.forEach(function(item) {
      item.color = getRandomColor();
    });

    $scope.newTodoText = '';

    $scope.addToDoItem = function (event, clickPlus) {
      if (clickPlus || event.which === 13) {
        $scope.todoList.unshift({
          text: $scope.newTodoText,
          color: getRandomColor(),
        });
        $scope.newTodoText = '';
      }
    };
  }
})();
