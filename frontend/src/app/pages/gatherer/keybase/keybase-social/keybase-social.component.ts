import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';

@Component({
    selector: 'ngx-keybase-social',
    templateUrl: './keybase-social.component.html',
    styleUrls: ['./keybase-social.component.scss']
})
export class KeybaseSocialComponent implements OnInit {
    @ViewChild('nbCardGraphs') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private keybaseSocial : any;
    private validation : any;

    constructor() {}

    ngOnInit() {
        console.log("Keybase Social Component");
        this.keybaseSocial = this.data.result[4].graphic[0].keysocial;
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
}
