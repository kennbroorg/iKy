import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-searches',
    templateUrl: './search-searches.component.html',
    styleUrls: ['./search-searches.component.scss']
})
export class SearchSearchesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchSearches', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchSearches : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchSearches = this.data.result[4].graphic[5].searches;
        console.log("Search Searches Component");
        console.log("Searches data", this.searchSearches);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
