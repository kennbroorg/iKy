(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'd3TreeMap', d3TreeMap);
    
    /** @ngInject */
    function d3TreeMap() {
        return {
          restrict: 'E',
          scope: {
            treedata: '='
          },

          link: function (scope, element) {

            var heightParent = element.parent()[0].offsetHeight;
            var widthParent = element.parent()[0].offsetWidth;

            var margin = {top: 20, right: 20, bottom: 20, left: 20},
               width = widthParent - margin.left - margin.right,
               height = heightParent - margin.top - margin.bottom - margin.top - margin.bottom;

            scope.renderTreemap = function(data) {

                while (element[0].firstChild) {
                    element[0].removeChild(element[0].firstChild);
                }

                var svg = d3.select(element[0])
                  .append("svg")
                  .attr('width', width)
                  .attr('height', height)
                  // .attr('width', width + margin.left + margin.right)
                  // .attr('height', height + margin.top + margin.bottom)
                  // .attr('id', 'svg_id')
                  .append("g");

                // .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
                //
                // var color = d3.scale.category20c(),
                var color = "#6be1d5",
                x = d3.scale.linear().range([0, width]),
                y = d3.scale.linear().range([0, height]),
                root = data,
                node = data;


                var treemap = d3.layout.treemap()
                    .round(false)
                    .size([width, height])
                    .sticky(true)
                    .value(function(d) { 
                        return d.total; });

                  var nodes = treemap.nodes(root)
                      .filter(function(d) {return !d.children; });
                  var cell = svg.selectAll("g")
                      .data(nodes)
                    .enter().append("svg:g")
                      .attr("class", "cell")
                      .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
                  cell.append("svg:rect")
                      .attr("width", function(d) { return d.dx - 1; })
                      .attr("height", function(d) { return d.dy - 1; })
                      .style("fill", color)
                      .style("stroke-opacity", 0)
                      .style("fill-opacity", 0.4);
                      //.style("opacity", 0.3);
                  cell.append("svg:text")
                      .attr("x", function(d) { return d.dx / 2; })
                      .attr("y", function(d) { return d.dy / 2; })
                      .attr("dy", ".35em")
                      .attr("text-anchor", "middle")
                      // .text(function(d) { return d.name + ": " + d.total; })
                      .text(function(d) { return d.name; })
                      .style("fill", "#B3FEFF")
                      .style("opacity", 1)
                      .style("overflow", "visible");
                  cell.append("svg:text")
                      .attr("x", function(d) { return d.dx / 2; })
                      .attr("y", function(d) { return d.dy / 2; })
                      .attr("dy", "18px")
                      .attr("text-anchor", "middle")
                      // .text(function(d) { return d.name + ": " + d.total; })
                      .text(function(d) { return d.total; })
                      .style("fill", "#B3FEFF")
                      .style("opacity", 1)
                      .style("overflow", "visible");
            }

          scope.$watch('treedata', function(){
              scope.renderTreemap(scope.treedata);
          });

          }
        };
      }

}());
