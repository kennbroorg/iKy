import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-mastodon-social',
    templateUrl: './mastodon-social.component.html',
    styleUrls: ['./mastodon-social.component.scss']
})
export class MastodonSocialComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private mastodonSocial : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Mastodon Social Component");
        this.mastodonSocial = this.data.result[4].graphic[1].social;
        this.validation = this.data.result[2].validation;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
