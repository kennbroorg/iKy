import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-hashtag',
    templateUrl: './search-hashtag.component.html',
    styleUrls: ['./search-hashtag.component.scss']
})
export class SearchHashtagComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchHashtag : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchHashtag = this.data.result[4].graphic[7].hashtags;
        console.log("Search Hashtag Component");
        console.log("Search data total", this.data);
        console.log("Search data", this.searchHashtag);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
