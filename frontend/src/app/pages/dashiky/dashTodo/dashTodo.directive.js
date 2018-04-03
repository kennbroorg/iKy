(function () {
  'use strict';

  angular.module('BlurAdmin.pages.dashiky')
      .directive('dashTodo', dashTodo);

  /** @ngInject */
  function dashTodo() {
    return {
      restrict: 'EA',
      controller: 'dashTodoController',
      templateUrl: 'app/pages/dashiky/dashTodo/dashTodo.html'
    };
  }
})();
