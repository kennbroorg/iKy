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
    private validation : any;

    private card: any;
    private width: number;
    private height: number;
    showLegend = true;
    showLabels = true;

    constructor() {}

    ngOnInit() {

        // console.log("Twitter Popularity Component");
        // this.card = this.cardContainer.nativeElement;
        // this.width = this.card.clientWidth;
        // this.height = this.width * 0.68;

        // this.twitterPopularity = this.data.result[4].graphic[1].popularity.map(this.arrayAdecuate);
        // this.validation = this.data.result[2].validation;

        // /* Validation */
        // switch(this.data.result[2].validation) {
        //     case 'hard':
        //         this.validation = 'success';
        //         break;
        //     case 'soft':
        //         this.validation = 'warning';
        //         break;
        //     case 'no':
        //         this.validation = 'danger';
        //         break;
        //     default:
        //         this.validation = 'danger';
        // }
    }

    ngAfterViewInit() {
        this.card = this.cardContainer.nativeElement;
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("CARD-------------------------------", this.card);
        console.log("WIDTH-------------------------------", this.width);
        console.log("HEIGHT-------------------------------", this.height);
        console.log("Twitter Popularity Component");

        this.twitterPopularity = this.data.result[4].graphic[1].popularity.map(this.arrayAdecuate);
        this.validation = this.data.result[2].validation;

        /* Validation */
        switch(this.data.result[2].validation) {
            case 'hard':
                this.validation = 'success';
                break;
            case 'soft':
                this.validation = 'warning';
                break;
            case 'no':
                this.validation = 'danger';
                break;
            default:
                this.validation = 'danger';
        }
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['title']) {
            array[index].name = array[index]['title'];
            delete array[index].title;  
        }
        return item;
    }

}
