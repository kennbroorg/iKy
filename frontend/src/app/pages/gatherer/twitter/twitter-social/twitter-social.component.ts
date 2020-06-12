import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-social',
    templateUrl: './twitter-social.component.html',
    styleUrls: ['./twitter-social.component.scss']
})
export class TwitterSocialComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterSocial', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterSocial : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.twitterSocial = this.data.result[4].graphic[0].social;
    }

    ngAfterViewInit() {

        console.log("Twitter Social Component");
        console.log(this.twitterSocial);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
