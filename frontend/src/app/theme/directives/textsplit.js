/**
 * Created by kennbro on 13/03/18.
 */

(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'textsplit', textsplit);
    
    /** @ngInject */
    function textsplit() {
        return {
          restrict: 'E',
          scope: { content2: '=phrases' },

          link: function (scope, element) {

              function arrangeCurrentPage() {
                for (var i = 0; i < content[currentPage].title.length; i++) {
                  $(".mutable:eq(" + currentPage + ") > .soup-title > .letter").eq(i).css({
                    left: $(".position-data:eq(" + currentPage + ") > .soup-title > .letter").eq(i).offset().left + "px",
                    top: $(".position-data:eq(" + currentPage + ") > .soup-title > .letter").eq(i).offset().top + "px",
                    color: "#111",
                    zIndex: 9001
                  });
                }
                for (var i = 0; i < content[currentPage].desc.length; i++) {
                  $(".mutable:eq(" + currentPage + ") > .soup-desc > .letter").eq(i).css({
                    left: $(".position-data:eq(" + currentPage + ") > .soup-desc > .letter").eq(i).offset().left + "px",
                    top: $(".position-data:eq(" + currentPage + ") > .soup-desc > .letter").eq(i).offset().top + "px",
                    color: "#111",
                    zIndex: 9001
                  });
                }
              }

              function setText() {
                var j;
                for (j = 0; j < content[i].title.length; j++) {
                  $(".soup-title").last().append("<span class=\"letter\">" + content[i].title[j] + "</span>");
                }
                for (j = 0; j < content[i].desc.length; j++) {
                  $(".soup-desc").last().append("<span class=\"letter\">" + content[i].desc[j] + "</span>");
                }
              }

              function scrambleOthers() {
                for (var i = 0; i < content.length; i++) {
                  //don't scramble currentPage
                  if (currentPage === i)
                    continue;
                  var parts = [
                    ["title", ".soup-title"],
                    ["desc", ".soup-desc"]
                  ];
                  //apply to .title h1s and .desc ps
                  for (var j = 0; j < parts.length; j++) {
                    for (var k = 0; k < content[i][parts[j][0]].length; k++) {
                      //define random position on screen
                      var randLeft = Math.floor(Math.random() * $(window).width());
                      var randTop = Math.floor(Math.random() * $(window).height());
                      //defining boundaries
                      var offset = $(".position-data").eq(currentPage).offset();
                      var bounds = {
                        left: offset.left,
                        top: offset.top,
                        right: $(window).width() - offset.left,
                        bottom: $(window).height() - offset.top
                      };
                      var middleX = bounds.left + $(".position-data").eq(currentPage).width() / 2;
                      var middleY = bounds.top + $(".position-data").eq(currentPage).height() / 2;
                      //finally, apply all the scrambles
                      $(".mutable:eq(" + i + ") > " + parts[j][1] + " > .letter").eq(k).css({
                        left: randLeft,
                        top: randTop,
                        color: "#DDD",
                        zIndex: "initial"
                      });
                    }
                  }
                }
              }




            scope.$watch('content2', function(content2) {


              console.log("content2", content2);

              var content = [{
                title: "Hi! I'm Justus Tumacder.",
                desc: "Welcome to my alphabet soup demo!"
              }, {
                title: "Lorem ipsum",
                desc: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
              }, {
                title: "dolor sit amet",
                desc: "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
              }, {
                title: "Grouping example",
                desc: [
                  ["<u>Grouped text</u>"], " separate text".split("")
                ]
              }];



              var currentPage = 0;
              console.log("content length", content.length);
              //generate content
              for (var i = 0; i < content.length; i++) {
                console.log("content split", content[i], i);
                //split content letters to array
                for (var obj in content[i]) {
                  //if string
                  if (typeof content[i][obj] === "string") {
                    content[i][obj] = content[i][obj].split("");
                    continue;
                  }
                  //if array (grouped text)
                  else if (typeof content[i][obj] === "object") {
                    var toPush = [];
                    for(var j = 0; j < content[i][obj].length; j++) {
                      for(var k = 0; k < content[i][obj][j].length; k++) {
                        toPush.push(content[i][obj][j][k]);
                      }
                    }
                    content[i][obj] = toPush;
                  }
                }

                console.log("content ", content);

                //set text to 
                $("#segments").append("<div class=\"letters-wrap mutable\"><div class=\"soup-title\"></div><div class=\"soup-desc\"></div></div>");
                setText();
                //clone to data
                $("#segments").append("<div class=\"letters-wrap position-data\"><div class=\"soup-title\"></div><div class=\"soup-desc\"></div></div>");
                setText();
              }


              $(window).resize(function() {
                arrangeCurrentPage();
                scrambleOthers();
              });

              console.log("content", content);

              setInterval(function(){ 
                currentPage++;
                if (currentPage >= content.length){currentPage = 0};
                arrangeCurrentPage();
                scrambleOthers();
              }, 5000);





            })




          }
        };
      }

}());
