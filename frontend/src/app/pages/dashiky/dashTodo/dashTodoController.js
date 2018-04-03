/**
 * @author v.lugovksy
 * created on 16.12.2015
 */
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
      { text: 'Convert definitions in Trello boards' },
      { text: 'Continue the modification of pool task' },
      { text: 'Change logo by crazy graphics' },
      { text: 'Initial collection that runs other collectors' },
      { text: 'Cloud 3d Tag directive for profile' },
      { text: 'Vertical Tag for bios collected' },
      { text: 'Smart Profile' },
      { text: 'Contributors in dash, from based software and github contributions' },
      { text: 'Documentation for contributions' },
      { text: 'Normalize everything, python and angularjs' },
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
