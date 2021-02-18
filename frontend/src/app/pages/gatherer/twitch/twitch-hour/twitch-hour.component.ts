import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitch-hour',
    templateUrl: './twitch-hour.component.html',
    styleUrls: ['./twitch-hour.component.scss']
})
export class TwitchHourComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitchHour', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitchHour : any;

    private card: any;
    private width: number;
    private height: number;
    showLegend = false;
    showLabels = true;

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
        this.card = this.cardContainer.nativeElement;
    }

    ngAfterViewInit() {
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("Twitch Hour Component");
        console.log("Width", this.width);
        console.log("Height", this.height);

        this.twitchHour = this.data.result[4].graphic[5].hour;
        console.log("TwitchHour", this.twitchHour);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
