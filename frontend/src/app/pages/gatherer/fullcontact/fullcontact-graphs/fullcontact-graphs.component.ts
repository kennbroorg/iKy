import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { GraphsComponent } from '../../../shared/graphs/graphs.component';

@Component({
    selector: 'ngx-fullcontact-graphs',
    templateUrl: './fullcontact-graphs.component.html',
    styleUrls: ['./fullcontact-graphs.component.scss']
})
export class FullcontactGraphsComponent implements OnInit {
    @ViewChild('nbCardFullcontactGraphs') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private fullcontactGraphs : any;
    private validation : any;
  
    private card: any;
    private heightH: number;
  
    constructor() {}
  
    ngOnInit() {
        console.log("Fullcontact Graphs Component");
        console.log("Fullcontact data: ", this.fullcontactGraphs);
        this.fullcontactGraphs = this.data.result[4].graphic[0].social;
  
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
