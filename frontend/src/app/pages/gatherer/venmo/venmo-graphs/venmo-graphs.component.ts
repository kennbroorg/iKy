import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-venmo-graphs',
    templateUrl: './venmo-graphs.component.html',
    styleUrls: ['./venmo-graphs.component.scss']
})
export class VenmoGraphsComponent implements OnInit {
    @ViewChild('nbCardVenmoGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private venmoGraphs : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Venmo Graphs Component");
        this.venmoGraphs = this.data.result[4].graphic[0].user;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
