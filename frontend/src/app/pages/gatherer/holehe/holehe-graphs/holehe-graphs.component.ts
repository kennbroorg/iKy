import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';
import { NbPopoverDirective, NbPosition, NbTrigger } from '@nebular/theme';

@Component({
    selector: 'ngx-holehe-graph',
    templateUrl: './holehe-graphs.component.html',
    styleUrls: ['./holehe-graphs.component.scss']
})
export class HoleheGraphComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardHoleheGraph', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private holeheGraph : any;

    private validation : any;
    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.holeheGraph = this.data.result[4].graphic[0].holehe;
        this.validation = this.data.result[2].validation;
        console.log("Holehe Graph Component");
        console.log("Holehe data", this.holeheGraph);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
