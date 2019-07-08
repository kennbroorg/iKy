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
  
    private card: any;
    private height: number;
    private width: number;

    private noData: string = "OK";
  
    constructor() {}
  
    ngOnInit() {
        console.log("Leak Graphs Component");
        this.leakGraphs = this.data.result[4].graphic[0].leaks;
        console.log("Leak data: ", this.leakGraphs);

        this.card = this.nbCardContainer.nativeElement;
        // this.width = this.nbCardContainer.nativeElement.parentNode.parentNode.clientWidth;
        // this.height = this.nbCardContainer.nativeElement.parentNode.parentNode.clientHeight;
        console.log("CARD----F--------------------------", this.card);
        // console.log("WIDTH---F---------------------------", this.width);
        // console.log("HEIGHT--F----------------------------", this.height);

        if (this.data.result[3].raw[0].title != null) {
            this.noData = this.data.result[3].raw[0].title;
        }
        console.log("Leak noData: ", this.noData);
    }
}
