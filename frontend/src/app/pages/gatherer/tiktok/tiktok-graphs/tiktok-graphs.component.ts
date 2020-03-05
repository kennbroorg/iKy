import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-tiktok-graphs',
    templateUrl: './tiktok-graphs.component.html',
    styleUrls: ['./tiktok-graphs.component.scss']
})
export class TiktokGraphsComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private tiktokGraphs : any;
    private statusFull : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Tiktok Graphs Component");
        this.tiktokGraphs = this.data.result[4].graphic[0].tiktok;
        this.validation = this.data.result[2].validation;

        try {
             this.statusFull = this.data.result[3].raw.status;
        }
        catch (e) {
             this.statusFull = "";
        }
        console.log(`Status: ${this.statusFull}`);
        console.log(`Status: ${this.data.result[3].raw}`);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
