import { Component,
    OnInit,
    OnChanges,
    ViewChild,
    ElementRef,
    Input,
    ViewEncapsulation,
    AfterViewInit } from '@angular/core';
import * as $ from 'jquery';
import * as d3 from 'd3';
import {event as d3Event} from 'd3-selection';
import {zoom as d3Zoom} from 'd3-zoom';
import {drag as d3Drag} from 'd3-drag';
import {select as d3Select} from 'd3-selection';

@Component({
    selector: 'ngx-circle-social',
    templateUrl: './circle-social.component.html',
    styleUrls: ['./circle-social.component.scss'],
})
export class CircleSocialComponent implements OnInit, AfterViewInit {
  @ViewChild('cardCircleSocial', { static: false }) private cardContainer: ElementRef;
  @Input() private data: Array<any>;

  private width: number;
  private height: number;
  private element: any;
  private card: any;
  private diameter: any;

  constructor() {}

  ngOnInit() {
      // this.card = this.cardContainer.nativeElement;
      // this.width = this.card.clientWidth;
      // this.height = this.width * 0.68;
      // this.diameter = this.height;
      // this.drawChart(this.card, this.data, this.height, this.width, this.diameter);
  }

  ngAfterViewInit() {
      this.card = this.cardContainer.nativeElement;
      this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
      this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight;
      this.diameter = this.height;
      this.drawChart(this.card, this.data, this.height, this.width, this.diameter);
  }

    drawChart(element, data, height, width, diameter) {

      const presence = {'name': 'presence', 'children': data};
      const root = d3.hierarchy(presence);

      const format = d3.format(',d');

      const packLayout = d3.pack();

      packLayout.size([width - 4, height - 4]);

      root.sum(function(d: any) {
        return d.value;
      });

      packLayout(root);

      const svg = d3.select(element).append('svg')
          .attr('width', width)
          .attr('height', height)
          .attr('class', 'bubble');

      const node = svg.selectAll('.node')
          .data(root.descendants())
        .enter().append('g')
          .attr('class', 'node')
          .attr('transform', function(d: any) { return 'translate(' + d.x + ',' + d.y + ')'; });
      node.append('circle')
          .attr('r', function(d: any) { return d.r; })
          .style('fill', 'rgba(5, 252, 252, 0.1)');
          // .style('fill', 'rgba(5, 252, 252, 0.3)');

      node.append('svg:title')
          .text(function(d: any) { return d.data.name + (d.children ? '' : ': ' + format(d.value)); });

      node.filter(function(d: any) { return !d.children; }).append('svg:text')
          .attr('text-anchor', 'middle')
          .attr('dy', '0')
          .attr('fill', '#05fcfc')
          .text(function(d: any) { return d.data.name.substring(0, d.r / 3); });

      // node.filter(function(d: any) { return d.children; }).append('svg:text')
      node.filter(function(d: any) { if (d.data.name !== 'presence') { return d.children; } }).append('svg:text')
          .attr('text-anchor', 'middle')
          .attr('dy', function(d: any) { return d.r * -0.5; })
          .attr('fill', '#05fcfc')
          .attr('stroke', '#05fcfc')
          .text(function(d: any) { return d.data.name.substring(0, d.r / 3); });
    }
}
