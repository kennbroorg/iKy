import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-tiktok-graphs',
    templateUrl: './tiktok-graphs.component.html',
    styleUrls: ['./tiktok-graphs.component.scss'],
})
export class TiktokGraphsComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private tiktokGraphs: any;
    // private statusFull: any;
    private validation: any;
    public status: any;
    public messages: any;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log('Tiktok Graphs Component');
        console.log('Tiktok Graphs Component2');
        try {
          this.tiktokGraphs = this.data.result[4].graphic[0].tiktok;
        } catch (error) {
          this.tiktokGraphs = {};
        }

        this.validation = this.data.result[2].validation;

        try {
          //   this.statusFull = this.data.result[3].raw.status;
          this.status = this.data.result[3].raw[0].code;
          this.messages = this.data.result[3].raw[0].reason;
        } catch (e) {
          //   this.statusFull = '';
          this.status = 0;
          this.messages = '';
        }
        console.log('Tiktok Graphs Component3');
        console.log('Status: ', this.status);
        console.log(`Status: ${this.status}`);
        console.log(`Status: ${this.messages}`);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
