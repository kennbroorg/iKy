import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-hashtag',
    templateUrl: './twitter-hashtag.component.html',
    styleUrls: ['./twitter-hashtag.component.scss']
})
export class TwitterHashtagComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterHashtag') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterHashtag : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor() {}

    ngOnInit() {
        this.twitterHashtag = this.data.result[4].graphic[3].hashtag;
        this.validation = this.data.result[2].validation;
    }

    ngAfterViewInit() {
        // this.card = this.cardContainer.nativeElement;
        // console.log(this.card);
        // this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        // this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("Twitter Hashtag Component");
        console.log(this.twitterHashtag);

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
}
