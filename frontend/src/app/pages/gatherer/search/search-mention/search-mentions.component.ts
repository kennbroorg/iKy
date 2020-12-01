import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-search-mentions',
    templateUrl: './search-mentions.component.html',
    styleUrls: ['./search-mentions.component.scss']
})
export class SearchMentionsComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardMentionsHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private searchMentions : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.searchMentions = this.data.result[4].graphic[6].mentions;
        console.log("Search Mentions Component");
        console.log("Mentions data", this.searchMentions);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
