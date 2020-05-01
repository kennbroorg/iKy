import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-reddit-social',
    templateUrl: './reddit-social.component.html',
    styleUrls: ['./reddit-social.component.scss']
})
export class RedditSocialComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private redditSocial : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Reddit Social Component");
        this.redditSocial = this.data.result[4].graphic[0].social;
        this.validation = this.data.result[2].validation;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
