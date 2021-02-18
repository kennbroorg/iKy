import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitch-list',
    templateUrl: './twitch-list.component.html',
    styleUrls: ['./twitch-list.component.scss'],
})
export class TwitchListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardTwitchList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitchList : any;
    private twitchThumb : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.twitchList = this.data.result[4].graphic[1].table;
        this.twitchThumb = this.data.result[4].graphic[3].thumbnail;
        console.log("Twitch List Component");
        console.log("Twitch List data", this.twitchList);
        console.log("Twitch Thumbnail data", this.twitchThumb);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
