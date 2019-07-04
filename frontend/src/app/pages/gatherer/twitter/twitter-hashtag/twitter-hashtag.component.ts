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

    private card: any;
    private width: number;
    private height: number;

    constructor() {}

    ngOnInit() {
        this.twitterHashtag = this.data.result[4].graphic[3].hashtag;
    }

    ngAfterViewInit() {
        console.log("Twitter Hashtag Component");
        console.log(this.twitterHashtag);
    }
}
