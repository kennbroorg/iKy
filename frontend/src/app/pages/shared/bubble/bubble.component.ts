import { Component, OnInit, OnChanges, ViewChild, ElementRef, Input, ViewEncapsulation, AfterViewInit } from '@angular/core';
import * as $ from 'jquery';
import * as d3 from 'd3';
import {event as d3Event} from 'd3-selection';
import {zoom as d3Zoom} from 'd3-zoom';
import {drag as d3Drag} from 'd3-drag';
import {select as d3Select} from 'd3-selection';

@Component({
    selector: 'ngx-bubble',
    templateUrl: './bubble.component.html',
    styleUrls: ['./bubble.component.scss']
})
export class BubbleComponent implements OnInit, AfterViewInit {
    @ViewChild('cardBubble', { static: false }) private cardContainer: ElementRef;
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
      console.log("CARD-------------------------------", this.card);
      console.log("WIDTH-------------------------------", this.width);
      console.log("HEIGHT-------------------------------", this.height);
      this.drawChart(this.card, this.data, this.height, this.width, this.diameter);
  }

    drawChart(element, data, height, width, diameter) {

        var format = d3.format(",d"),
            color = d3.scaleOrdinal(d3.schemeCategory10);
        // color = d3.scaleOrdinal(d3.schemeCategory20c);
        var bubble = d3.pack()
         // .size([diameter, diameter])
            .size([width, height])
            .padding(1);
        var svg = d3.select(element).append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("class", "bubble");
  
        var root = d3.hierarchy({ "children" : data })
            .sum(function(d: any) { return d.value; })
            .sort(function(a, b) { return b.value - a.value; });
  
        bubble(root);
        var node = svg.selectAll(".node")
            .data(root.children)
          .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d: any) { return "translate(" + d.x + "," + d.y + ")"; });
        node.append("title")
            .text(function(d: any) { return d.data.name.concat(": ", d.data.value); });
        node.append("circle")
            .attr("r", function(d: any) { return d.r; })
            .style("fill", "#05fcfc");
        node.append("text")
            .attr("dy", ".3em")
            .attr('fill', '#000')
            .attr('font-size', "10px" )
            .style("text-anchor", "middle")
            .text(function(d: any) { return d.data.name; });
  
        d3.select(self.frameElement).style("height", diameter + "px");
    }
}
