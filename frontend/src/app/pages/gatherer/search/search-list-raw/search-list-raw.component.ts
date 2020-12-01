import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-list-raw',
    templateUrl: './search-list-raw.component.html',
    styleUrls: ['./search-list-raw.component.scss'],
})
export class SearchRawListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardSearchRawList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchRawList : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchRawList = this.data.result[4].graphic[3].rawresults;
        console.log("Search List Raw Component");
        console.log("Search List Raw data", this.searchRawList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
