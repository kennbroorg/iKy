/**
 * Created by kennbro on 13/03/18.
 */

(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'd3Relations', d3Relations);
    
    /** @ngInject */
    function d3Relations() {
        return {
          restrict: 'E',
          scope: {
            data: '='
          },

          link: function (scope, element) {

            var heightParent = element.parent()[0].offsetHeight;
            var widthParent = element.parent()[0].offsetWidth;

            var margin = {top: 15, right: 15, bottom: 60, left: 60},
              width = widthParent -50 - margin.left - margin.right,
              height = heightParent - 50 - margin.top - margin.bottom;

            var force = getForce(height, width);
            var color = getColor();

            var chart = d3.select(element[0])
              .append("svg")
              .attr('width', width + margin.left + margin.right)
              .attr('height', height + margin.top + margin.bottom)
              .attr('id', 'svg_id')
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


            function getForce(height, width) {
                  return d3.layout.force()
                      .charge(-820)
                      .linkDistance(100)
                      .size([width, height]);
            }

            function getColor() {
                  return d3.scale.category10();
            }


            scope.render = function(data) {

              if (data === undefined) {
                return ;
              }

              chart.selectAll("*").remove();

              data = readData(data);
              drawPlot(chart, force, color, data);



              function readData(data) {

                  var id = 0;
                  var cache = {};
                  var list = [];
                  var links = [];

                  function Node(name, adds) {
                      this.id = id++;
                      this.name = name;
                      list.push(this);
                      cache[this.name] = this;
                      if (adds) {
                          for (var key in adds) {
                              this[key] = adds[key];
                          }
                      }
                  }
                  function getInfo(name, picture, subtitle, icon) {
                      if (name in cache) return cache[name];
                      return new Node(name, { picture: picture, group: 0, subtitle: subtitle, icon: icon });
                  }
                  function getLink(link, picture, subtitle, icon) {
                      var name = link
                      if (name in cache) return cache[name];
                      return new Node(name, { picture: picture, group: 1, subtitle: subtitle, icon: icon });
                  }
                  function addLinks(name, topic) {
                      links.push({ source: name.id, target: topic.id });
                  }

                  data.forEach(function (entry) {
                      var linkage = getLink(entry.link, entry.picture, entry.subtitle, entry.icon);
                      var title = getInfo(entry.title, entry.picture, entry.subtitle, entry.icon);
                      // linkage.usage++;
                      addLinks(title, linkage);
                  });
                  return { list: list, links: links };
              }


              function drawPlot(chart, force, color, data) {
                  force.nodes(data.list)
                      .links(data.links)
                      .start();

                  var link = chart.selectAll('.link')
                      .data(data.links)
                      .enter()
                      .append('line')
                        .attr('class', 'link')
                        .style('stroke', '#209E91')
                        .style('stroke-width', 1.5);

                  var node = chart.selectAll('.node')
                      .data(data.list)
                      .enter()
                      .append('g')
                        .call(force.drag);

                  node.append('circle')
                      .attr('r', 21)
                        .style('fill', function (d) {
                            if (d.group == 0) return '#209E91';
                            if (d.group == 1) return '#209E91';
                            return color(d.group);
                        });

                  node.each(function (d) {
                      if (!d.picture) return;
                      d3.select(this)
                          .append('image')
                            .attr('xlink:href', d.picture)
                            .attr('x', -15)
                            .attr('y', -15)
                            .attr('width', 30)
                            .attr('height', 30)
                            .attr('clip-path', 'url(#circle-clip-' + d.id + ')');
                      d3.select(this)
                          .append('clipPath')
                            .attr('id', 'circle-clip-' + d.id)
                          .append('circle').attr('r', 20);
                  });

                  node.each(function (d) {
                      var title = d.name;
                      var subtitle = d.subtitle;
                      var icon = d.icon;
                      d3.select(this).append('text')
                        .attr('text-anchor', 'middle')
                        .attr('alignment-baseline', 'middle')
                        .attr('fill', '#00FBFF')
                        .attr("y", -27)
                        .text(title);
                      d3.select(this).append('text')
                        .attr('text-anchor', 'middle')
                        .attr('alignment-baseline', 'middle')
                        .attr('fill', '#B3FEFF')
                        .attr("y", 30)
                        .text(subtitle);
                      if (icon) {
                        d3.select(this).append("text")
                          .attr("style","font-family:FontAwesome;")
                          .attr('text-anchor', 'middle')
                          .attr('alignment-baseline', 'central')
                          .attr('font-size', "30px" )
                          .attr('fill', "#222" )
                          // .attr("x", -13)
                          // .attr("y", 10)
                          // .text(icon);
                          .text(function(d) { 
                              return d.icon;
                          });
                      }
                  });


                  force.on('tick', function () {
                      link.attr('x1', function (d) {
                          return d.source.x;
                      }).attr('y1', function (d) {
                          return d.source.y;
                      }).attr('x2', function (d) {
                          return d.target.x;
                      }).attr('y2', function (d) {
                          return d.target.y;
                      });

                      node.attr('transform', function (d) {
                          return 'translate(' + d.x + ', ' + d.y + ')';
                      });
                  });
              };

          };

          scope.$watch('data', function(){
              scope.render(scope.data);
          });

          }
        };
      }

}());
