import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-social',
    templateUrl: './search-social.component.html',
    styleUrls: ['./search-social.component.scss']
})
export class SearchSocialComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchSocial', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchSocial : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchSocial = this.data.result[4].graphic[2].social;
        console.log("Search Social Component");
        console.log("Social data", this.searchSocial);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
