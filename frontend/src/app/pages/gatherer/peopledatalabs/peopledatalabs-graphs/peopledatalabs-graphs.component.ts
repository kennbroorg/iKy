import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-peopledatalabs-graphs',
    templateUrl: './peopledatalabs-graphs.component.html',
    styleUrls: ['./peopledatalabs-graphs.component.scss']
})
export class PeopledatalabsGraphsComponent implements OnInit {
    @ViewChild('nbCardPeopledatalabsGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private peopledatalabsGraphs : any;
    private statusFull : any;
    private statusMessages : any;
    private validation : any;
  
    private card: any;
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Peopledatalabs Graphs Component");
        this.peopledatalabsGraphs = this.data.result[4].graphic[0].data;
        console.log("Peopledatalabs data: ", this.peopledatalabsGraphs);
        this.statusFull = this.data.result[3].raw['status'];
        this.statusMessages = this.data.result[3].raw['error'];
        console.log("Peopledatalabs status: ", this.statusFull);
        console.log("Peopledatalabs Messages: ", this.statusMessages);
        console.log("Peopledatalabs Messages2: ", this.statusMessages.message);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
