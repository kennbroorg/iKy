import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-tinder-graphs',
    templateUrl: './tinder-graphs.component.html',
    styleUrls: ['./tinder-graphs.component.scss']
})
export class TinderGraphsComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private tinderGraphs : any;
    private statusFull : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Tinder Graphs Component");
        this.tinderGraphs = this.data.result[4].graphic[0].tinder;
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
