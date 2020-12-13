import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-holehe-list',
    templateUrl: './holehe-list.component.html',
    styleUrls: ['./holehe-list.component.scss'],
})
export class HoleheListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardHoleheList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private holeheList : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.holeheList = this.data.result[4].graphic[1].lists;
        console.log("Holehe List Component");
        console.log("Holehe List data", this.holeheList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
