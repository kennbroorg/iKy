import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-list',
    templateUrl: './twitter-list.component.html',
    styleUrls: ['./twitter-list.component.scss']
})
export class TwitterListComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterList') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterList : any;

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
        console.log("Twitter List Component");

        this.twitterList = this.data.result[4].graphic[5].tweetslist;
    }
}
