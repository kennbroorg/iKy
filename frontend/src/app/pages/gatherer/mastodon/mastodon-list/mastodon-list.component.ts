import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-mastodon-list',
    templateUrl: './mastodon-list.component.html',
    styleUrls: ['./mastodon-list.component.scss'],
})
export class MastodonListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardMastodonList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private mastodonList : any;
    // private validation : any;

    // private card: any;
    // private width: number;
    // private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.mastodonList = this.data.result[4].graphic[2].list;
        console.log("Mastodon List Raw Component");
        console.log("Mastodon List Raw data", this.mastodonList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
