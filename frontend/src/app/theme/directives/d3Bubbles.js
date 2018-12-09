(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'd3Bubbles', d3Bubbles);
    
    /** @ngInject */
    function d3Bubbles() {
        return {
          restrict: 'E',
          scope: {
            skilldata: '='
          },

          link: function (scope, element) {

            var heightParent = element.parent()[0].offsetHeight;
            var widthParent = element.parent()[0].offsetWidth;

            // var margin = {top: 20, right: 20, bottom: 20, left: 20},
            var margin = {top: 15, right: 15, bottom: 15, left: 15},
               width = widthParent - margin.left - margin.right,
               height = heightParent - margin.top - margin.bottom;

            var bleed = 100;
            console.log("height");
            console.log(height);
            var diameter = 600;

            scope.renderBubbles = function(data) {

                while (element[0].firstChild) {
                    element[0].removeChild(element[0].firstChild);
                }
                var svg = d3.select(element[0])
                  .append("svg")
                  .attr('width', width)
                  .attr('height', height - margin.bottom - margin.top)
                  .append("g")
                    .attr("transform", "translate(0," + -bleed + ")");

                var color = "#6be1d5"

                var pack = d3.layout.pack()
                        .sort(null)
                        .size([width, height + bleed * 1.5])
                        .padding(2);

                var force = d3.layout.force()
                    .size([width, height + bleed * 1.5]);

                force.nodes(data).start();
                var nodes = pack.nodes(data);

                var node = svg.selectAll(".node")
                        .data(nodes).enter()
                      .append("g")
                        .attr("class", "node")
                        .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
                //     .call(force.drag);

                node.append("circle")
                        .attr("r", function(d) { return d.r; })
  	                .attr("fill", function(d){ return d.children ? "#000000" : "#6be1d5"; }) //make nodes with children invisible
 	                .attr("opacity", function(d){ return d.children ? 0.0 : 0.4; }) //make nodes with children invisible

                node.append("text")
                        .attr("dy", ".3em")
                        .style("text-anchor", "middle")
                        .style("fill", "#B3FEFF")
                        .attr('font-size', "12px" )
                        .text(function(d) {
                            return d.name.substring(0, d.r / 2);
                        });

                node.append("title")
                    .text(function(d) {
                        return d.name + ": " + d.count;
                    });

                d3.select(self.frameElement)
                        .style("height", diameter + "px");
            }

          scope.$watch('skilldata', function(){
              scope.renderBubbles(scope.skilldata);
          });

          }

        };
      }

}());
