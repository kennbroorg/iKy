import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-mention',
    templateUrl: './instagram-mention.component.html',
    styleUrls: ['./instagram-mention.component.scss']
})
export class InstagramMentionComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardInstagramMention', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramMention : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.instagramMention = this.data.result[4].graphic[4].mentions;
        console.log("Instagram Mention Component");
        console.log(this.instagramMention);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
