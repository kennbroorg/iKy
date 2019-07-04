import { Component, OnInit, OnDestroy, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-approval',
    templateUrl: './twitter-approval.component.html',
    styleUrls: ['./twitter-approval.component.scss']
})
export class TwitterApprovalComponent implements OnInit, AfterViewInit {
    showLegend = true;
    showLabels = true;
    themeSubscription: any;

    @ViewChild('nbCardTwitterApproval') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterApproval : any;

    private card: any;
    private width: number;
    private height: number;

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

        console.log("Twitter Approval Component");

        this.twitterApproval = this.data.result[4].graphic[2].approval.map(this.arrayAdecuate);

    }

    ngOnDestroy(): void {
        this.themeSubscription.unsubscribe();
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['title']) {
            array[index].name = array[index]['title'];
            delete array[index].title;  
        }
        return item;
    }
}
