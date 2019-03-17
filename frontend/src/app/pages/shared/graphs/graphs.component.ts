import { Component, OnInit, OnChanges, ViewChild, ElementRef, Input, ViewEncapsulation } from '@angular/core';
import * as $ from 'jquery';
import * as d3 from 'd3';
import {event as d3Event} from 'd3-selection';
import {zoom as d3Zoom} from 'd3-zoom';
import {drag as d3Drag} from 'd3-drag';
import {select as d3Select} from 'd3-selection';

@Component({
    selector: 'ngx-graphs',
    templateUrl: './graphs.component.html',
    styleUrls: ['./graphs.component.scss']
})
export class GraphsComponent implements OnInit {
  @ViewChild('cardGraphs') private cardContainer: ElementRef;
  @Input() private data: Array<any>;

  private width: number;
  private height: number;
  private element: any;
  private card: any;

  constructor() {}

  ngOnInit() {
      this.card = this.cardContainer.nativeElement;
      this.width = this.card.clientWidth;
      this.height = this.width * 0.68;
      this.drawChart(this.card, this.data, this.height, this.width);
  }

  drawChart(element, data, height, width) {
      // Read Data
      data = this.readData(data);
  
      // Create Chart
      var chart = this.createChart(element, height, width);
      var color = this.getColor();
  
      var force = this.getForce(height, width);
      this.drawPlot(chart, force, color, data);
  }

  readData(data) {

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
          addLinks(title, linkage);
      });
      return { list: list, links: links };
  }

    createChart(element, height, width) {
        return d3Select(element).append('svg')
        .attr('width', width)
        .attr('height', height);
    }

    getForce(height, width) {
        return d3.forceSimulation()
          .force("charge", d3.forceManyBody().strength(-820))
          .force("link", d3.forceLink().distance(60))
          .force("center", d3.forceCenter(width / 2, height / 2))
    }

    getColor() {
        return d3.scaleOrdinal(d3.schemeCategory10);
    }

    drawPlot(chart, force, color, data) {
        force.nodes(data.list);
        force.force("link").links(data.links);
        force.restart();
  
        var link = chart.selectAll('.link')
            .data(data.links)
            .enter()
            .append('line')
              .attr('class', 'link')
              // .style('stroke', '#209E91')
              .style('stroke', '#05fcfc')
              .style('stroke-width', 0.3)
              .style('opacity', 1);
  
        var node = chart.selectAll('.node')
            .data(data.list)
            .enter()
            .append('g')
              .call(d3Drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
  
        node.append('circle')
            .attr('r', 21)
              .style('fill-opacity', 0.7)
              .style('fill', function (d) {
                  if (d.group == 0) return '#05fcfc';
                  if (d.group == 1) return '#05fcfc';
                  return color(d.group);
              });
  
        node.each(function (d) {
            if (!d.picture) return;
            d3Select(this)
                .append('image')
                  .attr('xlink:href', d.picture)
                  .attr('x', -15)
                  .attr('y', -15)
                  .attr('width', 30)
                  .attr('height', 30)
                  .attr('clip-path', 'url(#circle-clip-' + d.id + ')');
            d3Select(this)
                .append('clipPath')
                  .attr('id', 'circle-clip-' + d.id)
                .append('circle').attr('r', 15);
        });
  
        // For picture
        node.each(function (d) {
            if (!d.picture) return;
            d3Select(this)
                .append('image')
                  .attr('xlink:href', d.picture)
                  .attr('x', -15)
                  .attr('y', -15)
                  .attr('width', 30)
                  .attr('height', 30)
                  .attr('clip-path', 'url(#circle-clip-' + d.id + ')');
            d3Select(this)
                .append('clipPath')
                  .attr('id', 'circle-clip-' + d.id)
                .append('circle').attr('r', 15);
        });
  
        node.each(function (d) {
            var title = d.name;
            var subtitle = d.subtitle;
            var icon = d.icon;
            d3Select(this).append('text')
              .attr('text-anchor', 'middle')
              .attr('alignment-baseline', 'middle')
              .attr('fill', '#00FBFF')
              .attr("y", -27)
              .text(title);
            d3Select(this).append('text')
              .attr('text-anchor', 'middle')
              .attr('alignment-baseline', 'middle')
              .attr('fill', '#B3FEFF')
              .attr("y", 30)
              .text(subtitle);
            if (icon) {
                d3Select(this).append('svg:foreignObject')
                    .attr('height', '20px')
                    .attr('width', '30px')
                    .attr('x', '-15px')
                    .attr('y', '-10px')
                    .attr('fill-opacity', 0.7)
                    .attr('opacity', 0.7)
                    .attr('font-size', "20px" )
                    .attr('fill', "#000" )
                    .attr('stroke', "#000" )
                    .attr('color', "#000" )
                    .html('<i class="' + icon + '"></i>');
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
  
        function dragstarted(d) {
            if (!d3Event.active) force.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
  
        function dragged(d) {
            d.fx = d3Event.x;
            d.fy = d3Event.y;
        }
  
        function dragended(d) {
            if (!d3Event.active) force.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }
}
