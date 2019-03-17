import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { BubbleComponent } from '../../../shared/bubble/bubble.component';

@Component({
    selector: 'ngx-linkedin-bubble',
    templateUrl: './linkedin-bubble.component.html',
    styleUrls: ['./linkedin-bubble.component.scss']
})
export class LinkedinBubbleComponent implements OnInit {
    @ViewChild('nbCardLinkedinBubble') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private linkedinBubble : any;
    private validation : any;

    constructor() {}

    ngOnInit() {
        console.log("Linkedin Bubble Component");
        this.linkedinBubble = this.data.result[4].graphic[1].skills.children;

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
