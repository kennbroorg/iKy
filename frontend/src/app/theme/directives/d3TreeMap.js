/**
 * Created by kennbro on 13/03/18.
 */

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
               height = heightParent - margin.top - margin.bottom;

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
                        console.log("Valores", d.total);
                        return d.total; });



                // var data2 = {
                //   "name": "twitter",
                //   "children": [
                //        {"name": "Followers", "total": 3938},
                //        {"name": "Following", "total": 3812},
                //        {"name": "Listed", "total": 6714},
                //        {"name": "Tweets", "total": 73},
                //        {"name": "Likes", "total": 74}
                //       ]
                //      };
            
                // var data = scope.treedata;

                  console.log("DATA", data);
                  // console.log("DATA2", data2);
                  var nodes = treemap.nodes(root)
                      .filter(function(d) {return !d.children; });
                  console.log("NODES", nodes);
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
                      .text(function(d) { console.log("text", d.name + ": " + d.total); return d.name + ": " + d.total; })
                      .style("fill", "#B3FEFF")
                      .style("opacity", 1);
                  console.log("CELL", cell);
                   // d3.select(window).on("click", function() { zoom(root); });
                   // d3.select("select").on("change", function() {
                    //treemap.value(this.value == "size" ? size : count).nodes(root);
                    // treemap.value((this.value == "total") ? total : (this.value == "building") ? building : (this.value == "ground") ? ground : cash).nodes(root);
                  //  zoom(node);
                  // });
                // function total(d) {
                //   return d.total;
                // }
                // function zoom(d) {
                //   var kx = width / d.dx, ky = height / d.dy;
                //   x.domain([d.x, d.x + d.dx]);
                //   y.domain([d.y, d.y + d.dy]);
                //   var t = svg.selectAll("g.cell").transition()
                //       .duration(d3.event.altKey ? 7500 : 750)
                //       .attr("transform", function(d) { return "translate(" + x(d.x) + "," + y(d.y) + ")"; });
                //   t.select("rect")
                //       .attr("width", function(d) { return kx * d.dx - 1; })
                //       .attr("height", function(d) { return ky * d.dy - 1; })
                //   t.select("text")
                //       .attr("x", function(d) { return kx * d.dx / 2; })
                //       .attr("y", function(d) { return ky * d.dy / 2; })
                //       .style("opacity", function(d) { return kx * d.dx > d.w ? 1 : 0; });
                //   node = d;
                //   d3.event.stopPropagation();
                // }
            }









          scope.$watch('treedata', function(){
              console.log("TREEDATA ", scope.treedata);
              scope.renderTreemap(scope.treedata);
          });

          }
        };
      }

}());
