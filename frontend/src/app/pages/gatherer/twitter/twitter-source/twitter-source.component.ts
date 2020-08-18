import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-source',
    templateUrl: './twitter-source.component.html',
    styleUrls: ['./twitter-source.component.scss']
})
export class TwitterSourceComponent implements OnInit, AfterViewInit {
    themeSubscription: any;

    @ViewChild('nbCardTwitterSource', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterSource : any;

    private card: any;
    private width: number;
    private height: number;

    // options
    showXAxis: boolean = true;
    showYAxis: boolean = true;
    gradient: boolean = false;
    showLegend: boolean = false;
    showXAxisLabel: boolean = true;
    yAxisLabel: string = 'Source';
    showYAxisLabel: boolean = true;
    xAxisLabel: string = 'Tweets';

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

        this.twitterSource = this.data.result[4].graphic[9].sources;
        console.log("Twitter Source Component", this.twitterSource);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
