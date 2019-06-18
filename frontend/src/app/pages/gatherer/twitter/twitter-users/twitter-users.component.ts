import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';

@Component({
    selector: 'ngx-twitter-users',
    templateUrl: './twitter-users.component.html',
    styleUrls: ['./twitter-users.component.scss']
})
export class TwitterUsersComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterUsers') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterUsers : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor() {}

    ngOnInit() {
        this.twitterUsers = this.data.result[4].graphic[4].users;
        this.validation = this.data.result[2].validation;
    }

    ngAfterViewInit() {
        console.log("Twitter Users Component");
        console.log(this.twitterUsers);

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
