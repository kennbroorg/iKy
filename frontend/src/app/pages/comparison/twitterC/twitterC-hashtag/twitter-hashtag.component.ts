import { Component, OnInit, Input, AfterViewInit, TemplateRef } from '@angular/core';
// import { ViewChild, ElementRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-hashtag',
    templateUrl: './twitter-hashtag.component.html',
    styleUrls: ['./twitter-hashtag.component.scss'],
})
export class TwitterCHashtagComponent implements OnInit, AfterViewInit {
    // @ViewChild('nbCardTwitterHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterHashtag: any;

    public card: any;
    public width: number;
    public height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.twitterHashtag = this.data.result[4].graphic[0].hashtag;
        console.log('Twitter Hashtag Component');
        console.log(this.twitterHashtag);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
