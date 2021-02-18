import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitch-duration',
    templateUrl: './twitch-duration.component.html',
    styleUrls: ['./twitch-duration.component.scss']
})
export class TwitchDurationComponent implements OnInit, AfterViewInit {
    themeSubscription: any;

    @ViewChild('nbCardTwitchDuration', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitchDuration : any;

    private card: any;
    private width: number;
    private height: number;

    // options
    showXAxis: boolean = true;
    showYAxis: boolean = true;
    gradient: boolean = false;
    showLegend: boolean = false;
    showXAxisLabel: boolean = true;
    yAxisLabel: string = 'Duration';
    showYAxisLabel: boolean = true;
    xAxisLabel: string = 'Videos';

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

        this.twitchDuration = this.data.result[4].graphic[2].duration;
        console.log("Twitch Duration Component", this.twitchDuration);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
