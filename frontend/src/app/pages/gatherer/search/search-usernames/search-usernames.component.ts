import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-usernames',
    templateUrl: './search-usernames.component.html',
    styleUrls: ['./search-usernames.component.scss']
})
export class SearchUsernamesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSearchUsernames', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchUsernames : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchUsernames = this.data.result[4].graphic[1].username;
        console.log("Search UserNames Component");
        console.log("Names data", this.searchUsernames);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
