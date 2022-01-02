import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-mentions',
    templateUrl: './dorks-mentions.component.html',
    styleUrls: ['./dorks-mentions.component.scss']
})
export class DorksMentionsComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardMentionsHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksMentions : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksMentions = this.data.result[4].graphic[5].mentions;
        console.log("Dorks Mentions Component");
        console.log("Mentions data", this.dorksMentions);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
