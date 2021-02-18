import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-error-graphs',
    templateUrl: './error-graphs.component.html',
    styleUrls: ['./error-graphs.component.scss']
})
export class ErrorGraphsComponent implements OnInit {
    @ViewChild('nbCardErrorGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private statusGraphs : any;
    private reasonGraphs : any;
    private titleGraphs : any;
    private codeGraphs : any;
    private tracebackGraphs : any;
    private iconGraphs : any;
  
    private card: any;
  
    constructor() {}
  
    ngOnInit() {
        console.log("Error Graphs Component");
        this.titleGraphs = this.data.result[0].module.toUpperCase();
        this.codeGraphs = this.data.result[3].raw[0].code;
        this.statusGraphs = this.data.result[3].raw[0].status;
        this.reasonGraphs = this.data.result[3].raw[0].reason;
        this.tracebackGraphs = this.data.result[3].raw[0].traceback;
        if (this.codeGraphs == 1) { // User not found
            this.iconGraphs = "fas fa-user-slash"
        }
        if (this.codeGraphs == 2) { // Keys not found
            this.iconGraphs = "fas fa-key"
        }
        if (this.codeGraphs == 3) { // Keys error
            this.iconGraphs = "fas fa-key"
        }
        if (this.codeGraphs == 4) { // Others
            this.iconGraphs = "fas fa-exclamation-triangle"
            // fas fa-exclamation-triangle
            // fas fa-exclamation-circle
            // fas fa-minus-circle
        }
        if (this.codeGraphs >= 10) { // Error bug
            this.iconGraphs = "fas fa-bug"
        }
    }
}
