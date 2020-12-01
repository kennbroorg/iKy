import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-email',
    templateUrl: './search-email.component.html',
    styleUrls: ['./search-email.component.scss']
})
export class SearchEmailComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchEmail', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchEmails : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchEmails = this.data.result[4].graphic[8].emails;
        console.log("Search Emails Component");
        console.log("Search Emails data", this.searchEmails);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
