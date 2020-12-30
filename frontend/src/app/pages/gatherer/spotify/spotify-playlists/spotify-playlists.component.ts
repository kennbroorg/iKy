import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-spotify-playlists',
    templateUrl: './spotify-playlists.component.html',
    styleUrls: ['./spotify-playlists.component.scss']
})
export class SpotifyPlaylistsComponent implements OnInit, AfterViewInit {
    themeSubscription: any;

    @ViewChild('nbCardSpotifyPlaylists', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private spotifyPlaylists : any;

    private card: any;
    private width: number;
    private height: number;

    // options
    showXAxis: boolean = true;
    showYAxis: boolean = true;
    gradient: boolean = false;
    showLegend: boolean = false;
    showXAxisLabel: boolean = true;
    yAxisLabel: string = 'Playlists';
    showYAxisLabel: boolean = true;
    xAxisLabel: string = 'Tracks';

    colorScheme = {
      domain: [ 
          '#80deea', 
          '#4dd0e1',
          '#26c6da', 
          '#00bcd4', 
          '#00acc1', 
          '#0097a7', 
          '#00838f', 
          '#006064'
      ]
    };

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
    }

    ngAfterViewInit() {
        this.card = this.cardContainer.nativeElement;
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;

        this.spotifyPlaylists = this.data.result[4].graphic[1].playlist;
        console.log("Spotify Playlists Component", this.spotifyPlaylists);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
