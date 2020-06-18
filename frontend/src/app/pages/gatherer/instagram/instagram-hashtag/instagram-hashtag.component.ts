import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-hashtag',
    templateUrl: './instagram-hashtag.component.html',
    styleUrls: ['./instagram-hashtag.component.scss']
})
export class InstagramHashtagComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardInstagramHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramHashtag : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.instagramHashtag = this.data.result[4].graphic[3].hashtags;
        console.log("Instagram Hashtag Component");
        console.log(this.instagramHashtag);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
