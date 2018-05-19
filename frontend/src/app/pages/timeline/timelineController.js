(function () {
  'use strict';

  angular.module('BlurAdmin.pages.timeline')
      .controller('timelineController', timelineController);

  /** @ngInject */
  function timelineController(localStorageService, $scope) {

    console.log('Initialize Controller Timeline');
     
    // Do something if not
    if(localStorageService.isSupported) {
        console.log("localStorage Supported");
    }

    // Control storage
    if (localStorageService.get('timeline')) {
        $scope.timeline = localStorageService.get('timeline');

        // By now only github for profile
        console.log("Timeline Controller ", $scope.timeline);
        
        // Sort timeline array by date
        $scope.timeline.sort(function(a, b){
            var dateA=a.date.toLowerCase(), dateB=b.date.toLowerCase()
            if (dateA > dateB) //sort string ascending
                return -1 
            if (dateA < dateB)
                return 1
            return 0 //default return value (no sorting)
        })

        var timelineBlocks = $('.cd-timeline-block'),
            offset = 0.8;

        //hide timeline blocks which are outside the viewport
        hideBlocks(timelineBlocks, offset);

        //on scolling, show/animate timeline blocks when enter the viewport
        $(window).on('scroll', function () {
          if (!window.requestAnimationFrame) {
            setTimeout(function () {
              showBlocks(timelineBlocks, offset);
            }, 100);
          } else {
            window.requestAnimationFrame(function () {
              showBlocks(timelineBlocks, offset);
            });
          }
        });

        function hideBlocks(blocks, offset) {
          blocks.each(function () {
            ( $(this).offset().top > $(window).scrollTop() + $(window).height() * offset ) && $(this).find('.cd-timeline-img, .cd-timeline-content').addClass('is-hidden');
          });
        }

        function showBlocks(blocks, offset) {
          blocks.each(function () {
            ( $(this).offset().top <= $(window).scrollTop() + $(window).height() * offset && $(this).find('.cd-timeline-img').hasClass('is-hidden') ) && $(this).find('.cd-timeline-img, .cd-timeline-content').removeClass('is-hidden').addClass('bounce-in');
          });
        }

    } else {
        delete $scope.timeline
    }

  }
})();
