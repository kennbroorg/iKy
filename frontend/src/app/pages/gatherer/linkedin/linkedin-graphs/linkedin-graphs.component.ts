import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';
// import { GraphsComponent } from '../../../shared/graphs/graphs.component';

@Component({
    selector: 'ngx-linkedin-graphs',
    templateUrl: './linkedin-graphs.component.html',
    styleUrls: ['./linkedin-graphs.component.scss']
})
export class LinkedinGraphsComponent implements OnInit {
    @ViewChild('nbCardLinkedinGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private linkedinGraphs : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Linkedin Graphs Component");
        this.linkedinGraphs = this.data.result[4].graphic[0].social;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
