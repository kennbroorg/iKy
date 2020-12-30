import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-spotify-words',
    templateUrl: './spotify-words.component.html',
    styleUrls: ['./spotify-words.component.scss']
})
export class SpotifyWordsComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSpotifyWords', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private spotifyWords : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.spotifyWords = this.data.result[4].graphic[3].words;
        console.log("Spotify Words Component");
        console.log(this.spotifyWords);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
