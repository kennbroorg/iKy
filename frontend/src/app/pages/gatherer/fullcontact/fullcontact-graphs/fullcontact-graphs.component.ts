import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

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
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Fullcontact Graphs Component");
        this.fullcontactGraphs = this.data.result[4].graphic[0].social;
        console.log("Fullcontact data: ", this.fullcontactGraphs);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
