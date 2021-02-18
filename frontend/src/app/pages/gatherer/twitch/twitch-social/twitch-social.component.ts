import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitch-social',
    templateUrl: './twitch-social.component.html',
    styleUrls: ['./twitch-social.component.scss']
})
export class TwitchSocialComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitchSocial', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitchSocial : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.twitchSocial = this.data.result[4].graphic[0].social;
    }

    ngAfterViewInit() {

        console.log("Twitch Social Component");
        console.log(this.twitchSocial);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
