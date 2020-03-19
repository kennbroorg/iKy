import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-sherlock-graph',
    templateUrl: './sherlock-graphs.component.html',
    styleUrls: ['./sherlock-graphs.component.scss']
})
export class SherlockGraphComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSherlockGraph', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private sherlockGraph : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.sherlockGraph = this.data.result[4].graphic[0].sherlock;
        console.log("Sherlock Graph Component");
        console.log("Sherlock data", this.sherlockGraph);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
