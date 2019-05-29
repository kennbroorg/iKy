import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { GraphsComponent } from '../../../shared/graphs/graphs.component';

@Component({
    selector: 'ngx-leak-graphs',
    templateUrl: './leak-graphs.component.html',
    styleUrls: ['./leak-graphs.component.scss']
})
export class LeakGraphsComponent implements OnInit {
    @ViewChild('nbCardLeakGraphs') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private leakGraphs : any;
    private validation : any;
  
    private card: any;
    private heightH: number;
  
    constructor() {}
  
    ngOnInit() {
        console.log("Leak Graphs Component");
        this.leakGraphs = this.data.result[4].graphic[0].leaks;
        console.log("Leak data: ", this.leakGraphs);
  
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
