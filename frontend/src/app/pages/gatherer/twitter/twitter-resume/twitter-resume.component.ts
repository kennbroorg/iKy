import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-resume',
    templateUrl: './twitter-resume.component.html',
    styleUrls: ['./twitter-resume.component.scss']
})
export class TwitterResumeComponent implements OnInit, AfterViewInit {

    @ViewChild('nbCardTwitterResume') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterResume : any;

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

    private card: any;
    private width: number;
    private height: number;

    constructor() {}

    ngOnInit() {
    }

    ngAfterViewInit() {
        this.card = this.cardContainer.nativeElement;
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("Twitter Resume Component");

        this.twitterResume = this.data.result[4].graphic[0].resume.children.map(this.arrayAdecuate);
        console.log("Twitter Resume data", this.twitterResume);
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['total']) {
            array[index].value = array[index]['total'];
            delete array[index].total;  
        }
        return item;
    }

}
