import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-list-raw',
    templateUrl: './dorks-list-raw.component.html',
    styleUrls: ['./dorks-list-raw.component.scss'],
})
export class DorksRawListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardDorksRawList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksRawList : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksRawList = this.data.result[4].graphic[3].rawresults;
        console.log("Dorks List Raw Component");
        console.log("Dorks List Raw data", this.dorksRawList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
