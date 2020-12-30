import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-spotify-lang',
    templateUrl: './spotify-lang.component.html',
    styleUrls: ['./spotify-lang.component.scss']
})
export class SpotifyLangComponent implements OnInit {
    @ViewChild('nbCardSpotifyLang', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private spotifyLang : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Spotify Lang Component");
        // this.spotifyLang = this.data.result[4].graphic[4].lang.children;
        this.spotifyLang = this.data.result[4].graphic[4].lang;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
