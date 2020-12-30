import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-spotify-autors',
    templateUrl: './spotify-autors.component.html',
    styleUrls: ['./spotify-autors.component.scss']
})
export class SpotifyAutorsComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardSpotifyAutors', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private spotifyAutors : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.spotifyAutors = this.data.result[4].graphic[2].autors;
        console.log("Spotify Autors Component");
        console.log(this.spotifyAutors);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
