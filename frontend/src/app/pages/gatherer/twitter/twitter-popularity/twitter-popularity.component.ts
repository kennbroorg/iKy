import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-popularity',
    templateUrl: './twitter-popularity.component.html',
    styleUrls: ['./twitter-popularity.component.scss']
})
export class TwitterPopularityComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterPopularity') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterPopularity : any;

    private card: any;
    private width: number;
    private height: number;
    showLegend = true;
    showLabels = true;

    colorScheme = {
      domain: [ 
          '#80deea', 
          '#4dd0e1',
          '#26c6da', 
          '#00bcd4', 
          '#00acc1', 
          '#0097a7', 
          '#00838f', 
          '#006064'
      ]
    };

    constructor() {}

    ngOnInit() {
    }

    ngAfterViewInit() {
        this.card = this.cardContainer.nativeElement;
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("Twitter Popularity Component");

        this.twitterPopularity = this.data.result[4].graphic[1].popularity.map(this.arrayAdecuate);
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['title']) {
            array[index].name = array[index]['title'];
            delete array[index].title;  
        }
        return item;
    }

}
