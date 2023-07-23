import { Component, OnInit, Input, Output, EventEmitter, ViewEncapsulation,
  ChangeDetectionStrategy, ViewChild, ElementRef, AfterViewInit, TemplateRef,
  NgZone, ChangeDetectorRef } from '@angular/core';
import {Location} from '@angular/common';
import { scaleLinear, scaleTime, scaleBand } from 'd3-scale';
import { brushX } from 'd3-brush';
import { select, event as d3event } from 'd3-selection';
import {
  BaseChartComponent,
  ColorHelper,
  ViewDimensions,
  calculateViewDimensions,
  id,
  SingleSeries,
} from '@swimlane/ngx-charts';
import { NbDialogService } from '@nebular/theme';

@Component({
  // tslint:disable-next-line: component-selector
  selector: 'ngx-twitter-timeline',
  templateUrl: './twitter-timeline.component.html',
  styleUrls: ['./twitter-timeline.component.scss'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TwitterTimelineComponent extends BaseChartComponent implements OnInit, AfterViewInit {
  @ViewChild('nbCardTwitterTimeline', { static: true }) private cardContainer: ElementRef;
  @Input() autoScale = true;
  @Input() schemeType: string = 'ordinal';
  @Input() valueDomain: number[];
  @Input() xAxis: boolean = true;
  @Input() yAxis: boolean = true;
  @Input() showXAxisLabel: boolean = false;
  @Input() showYAxisLabel: boolean = false;
  @Input() xAxisLabel: string = 'yAxisLabel';
  @Input() yAxisLabel: string = 'xAxisLabel';
  @Input() gradient: boolean = false;
  @Input() showGridLines: boolean = true;
  @Input() animations: boolean = true;
  @Input() noBarWhenZero: boolean = true;

  @Output() onFilter = new EventEmitter();

  @Input() data: any;

  twitterTimeline: any;
  series: any;
  results: any;
  res_date: any;
  card: any;
  width: number;
  height: number;

  dims: ViewDimensions;
  xSet: any;
  xDomain: any;
  yDomain: any;
  seriesDomain: any;
  yScale: any;
  xScale: any;
  xAxisHeight: number = 0;
  yAxisWidth: number = 0;
  timeScale: any;
  colors: ColorHelper;
  scaleType: string;
  transform: string;
  margin: any[] = [0, 0, 20, 20];
    // margin: any[] = [10, 20, 10, 0];
  initialized: boolean = false;
  filterId: any;
  filter: any;
  brush: any;
  large: boolean = false;

  constructor(chartElement: ElementRef, zone: NgZone, cd: ChangeDetectorRef,
    location: Location, public dialogService: NbDialogService) {
    super(chartElement, zone, cd);
  }

    // constructor(chartElement: ElementRef, zone: NgZone, cd: ChangeDetectorRef, location: Location, dialogService: NbDialogService) {
    //  super(chartElement, zone, cd, location);
    // }

  ngOnInit() {
      this.card = this.cardContainer.nativeElement;
      console.log('Twitter Timeline Component');
  }

  ngAfterViewInit() {
      this.width = this.cardContainer.nativeElement.parentNode.clientWidth;
      this.height = this.cardContainer.nativeElement.parentNode.clientHeight;
      console.log('Twitter Timeline Component');

      this.res_date = this.twitterTimelineConvert();
      this.twitterTimeline = this.res_date;

      console.log('!!! RESULT DATE en init', this.res_date);
      // console.log('!!! Width', this.width);
      // console.log('!!! Height', this.height);
      // console.log('!!! yAxis', this.yAxis);
      // console.log('!!! yScale', this.yScale);
      // console.log('!!! dims', this.dims);
      // console.log('!!! showGridLines', this.showGridLines);
      // console.log('!!! showYAxisLabel', this.showYAxisLabel);
      // console.log('!!! yAxisLabel', this.yAxisLabel);
      // console.log('!!! xScale', this.xScale);
      // console.log('!!! yScale', this.yScale);
      // console.log('!!! colors', this.colors);
      // console.log('!!! gradient', this.gradient);
      // console.log('!!! animations', this.animations);
      // console.log('!!! noBarWhenZero', this.noBarWhenZero);
      this.update();
  }

  openDialog(dialog: TemplateRef<any>) {
    this.dialogService.open(dialog)
      .onClose.subscribe(result => {
        console.log('Event Close');
        this.large = false;
        this.update();
      });
    this.dims = calculateViewDimensions({
      width: this.width * 1.6,
      height: this.height * 1.6,
      margins: this.margin,
      showXAxis: this.xAxis,
      showYAxis: this.yAxis,
      xAxisHeight: this.xAxisHeight,
      yAxisWidth: this.yAxisWidth,
      showXLabel: this.showXAxisLabel,
      showYLabel: this.showYAxisLabel,
      showLegend: false,
      legendType: this.schemeType,
    });
    this.large = true;
    this.update();
  }

  twitterTimelineConvert(): SingleSeries {
    const res_conv: SingleSeries = [];

    console.log('!!! DATA', this.data.result[4].graphic[10].time);

    for (const d of this.data.result[4].graphic[10].time) {
      res_conv.push({
        name: new Date(d.name),
        value: d.value,
      });
    }
    return res_conv;
  }

  update(): void {
    // this.series = this.twitterTimeline;
    //  console.log("!!!!! RESULT - Update - Prev", this.results);
    //  this.results = this.twitterTimelineBarData();
    //  this.series = this.twitterTimelineBarData();
    this.results = this.res_date;
    //  console.log("!!!!! RESULT - Update - Prev 2", this.results);
    super.update();
    this.dims = calculateViewDimensions({
      width: this.width,
      height: this.height,
      margins: this.margin,
      showXAxis: this.xAxis,
      showYAxis: this.yAxis,
      xAxisHeight: this.xAxisHeight,
      yAxisWidth: this.yAxisWidth,
      showXLabel: this.showXAxisLabel,
      showYLabel: this.showYAxisLabel,
      showLegend: false,
      legendType: this.schemeType,
    });

    console.log('!!!!! DIMS Prev', this.dims);
    if (this.large) {
        this.dims['height'] = this.height * 1.6;
        this.dims['width'] = this.width * 1.6;
    } else {
        this.dims['height'] = this.height - 130;
        this.dims['width'] = this.width - 100;
    }
    console.log('!!!!! DIMS Post', this.dims);

    this.xDomain = this.getXDomain();

    this.yDomain = this.getYDomain();
    this.timeScale = this.getTimeScale(this.xDomain, this.dims.width);
    this.xScale = this.getXScale(this.xSet, this.dims.width);
    this.yScale = this.getYScale(this.yDomain, this.dims.height);

    this.setColors();
    this.transform = `translate(${this.dims.xOffset} , ${this.margin[0]})`;

    if (this.brush) {
      this.updateBrush();
    }

    this.filterId = 'filter' + id().toString();
    this.filter = `url(#${this.filterId})`;

    if (!this.initialized) {
      this.addBrush();
      this.initialized = true;
    }
    console.log('!!!!! xDomain', this.xDomain);
    console.log('!!!!! yDomain', this.yDomain);
    console.log('!!!!! timeScale', this.timeScale);
    console.log('!!!!! xScale', this.xScale);
    console.log('!!!!! yScale', this.yScale);
  }

  getXDomain(): any[] {
    const values = [];

    console.log('!!! getXDomain - Input', this.results);
    for (const d of this.results) {
      if (!values.includes(d.name)) {
        values.push(d.name);
      }
    }
    console.log('!!! getXDomain - values', values);

    this.scaleType = this.getScaleType(values);
    console.log('!!! getXDomain - scaleType', this.scaleType);
    let domain = [];

    const min = new Date(Math.min(...values));
    console.log('!!! getXDomain - Min value', min);
    min.setHours(0);
    min.setMinutes(0);
    min.setSeconds(0);

    const max = new Date(Math.max(...values));
    console.log('!!! getXDomain - Max value', max);
    max.setHours(23);
    max.setMinutes(59);
    max.setSeconds(59);

    domain = [min.getTime(), max.getTime()];
    console.log('!!! getXDomain - domain', domain);

    this.xSet = values;
    console.log('!!! getXDomain - xSet', this.xSet);
    return domain;
  }

  getYDomain(): any[] {
    if (this.valueDomain) {
      return this.valueDomain;
    }

    const domain = [];

    console.log('!!! getYDomain - input', this.results);
    for (const d of this.results) {
      if (domain.indexOf(d.value) < 0) {
        domain.push(d.value);
      }
      if (d.min !== undefined) {
        if (domain.indexOf(d.min) < 0) {
          domain.push(d.min);
        }
      }
      if (d.max !== undefined) {
        if (domain.indexOf(d.max) < 0) {
          domain.push(d.max);
        }
      }
    }
    console.log('!!! getYDomain - domain', domain);


    let min = Math.min(...domain);
    const max = Math.max(...domain);
    if (!this.autoScale) {
      min = Math.min(0, min);
    }

    // KKK
    min = 0;

    return [min, max];
  }

  getXScale(domain: any, width: any): any {
    return scaleBand().range([0, width]).paddingInner(0.1).domain(domain);
  }

  getTimeScale(domain: any, width: any): any {
    return scaleTime().range([0, width]).domain(domain);
  }

  getYScale(domain: any, height: any): any {
    const scale = scaleLinear().range([height, 0]).domain(domain);

    return scale;
  }

  getScaleType(values: any): string {
    return 'time';
  }

  trackBy(index: any, item: any): string {
    return item.name;
  }

  setColors(): void {
    let domain: any;
    if (this.schemeType === 'ordinal') {
      domain = this.xSet;
    } else {
      domain = this.yDomain;
    }
    this.scheme = 'aqua';

    this.colors = new ColorHelper(this.scheme, this.schemeType, domain, this.customColors);
  }

  updateYAxisWidth({ width }): void {
    this.yAxisWidth = width;
    this.update();
  }

  updateXAxisHeight({ height }): void {
    this.xAxisHeight = height;
    this.update();
  }

  addBrush(): void {
    if (this.brush) return;

    const height = this.height;
    const width = this.width;

    this.brush = brushX()
      .extent([
        [0, 0],
        [width, height],
      ])
      .on('brush end', () => {
        const selection = d3event.selection || this.xScale.range();
        const newDomain = selection.map(this.timeScale.invert);

        this.onFilter.emit(newDomain);
        this.cd.markForCheck();
      });

    select(this.chartElement.nativeElement).select('.brush').call(this.brush);
  }

  updateBrush(): void {
    if (!this.brush) return;

    const height = this.dims.height;
    const width = this.dims.width;

    this.brush.extent([
      [0, 0],
      [width, height],
    ]);
    select(this.chartElement.nativeElement).select('.brush').call(this.brush);

    // clear hardcoded properties so they can be defined by CSS
    select(this.chartElement.nativeElement)
      .select('.selection')
      .attr('fill', undefined)
      .attr('stroke', undefined)
      .attr('fill-opacity', undefined);

    this.cd.markForCheck();
  }
}
