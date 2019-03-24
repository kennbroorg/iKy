import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { GraphsComponent } from '../../../shared/graphs/graphs.component';

@Component({
    selector: 'ngx-linkedin-graphs',
    templateUrl: './linkedin-graphs.component.html',
    styleUrls: ['./linkedin-graphs.component.scss']
})
export class LinkedinGraphsComponent implements OnInit {
    @ViewChild('nbCardLinkedinGraphs') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private linkedinGraphs : any;
    private validation : any;

    constructor() {}

    ngOnInit() {
        console.log("Linkedin Graphs Component");
        this.linkedinGraphs = this.data.result[4].graphic[0].social;

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
        console.log("Validation : ", this.validation);
    }
}
