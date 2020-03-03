import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-names',
    templateUrl: './search-names.component.html',
    styleUrls: ['./search-names.component.scss']
})
export class SearchNamesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchNames', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchNames : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchNames = this.data.result[4].graphic[0].names;
        console.log("Search Names Component");
        console.log("Names data", this.searchNames);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
