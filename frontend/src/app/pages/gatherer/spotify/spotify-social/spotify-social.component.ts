import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-spotify-social',
    templateUrl: './spotify-social.component.html',
    styleUrls: ['./spotify-social.component.scss']
})
export class SpotifySocialComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSpotifySocial', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private spotifySocial : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.spotifySocial = this.data.result[4].graphic[0].social;
    }

    ngAfterViewInit() {

        console.log("Spotify Social Component");
        console.log(this.spotifySocial);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
