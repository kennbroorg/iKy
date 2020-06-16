import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-tweetiment-lines',
    templateUrl: './tweetiment-lines.component.html',
    styleUrls: ['./tweetiment-lines.component.scss']
})
export class TweetimentLinesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTweetimentLines', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private tweetimentLines : any;

    private card: any;
    private width: number;
    private height: number;
    // options
    legend: boolean = true;
    showLabels: boolean = true;
    animations: boolean = true;
    xAxis: boolean = false;
    yAxis: boolean = true;
    // yAxis: boolean = false;
    showYAxisLabel: boolean = true;
    showXAxisLabel: boolean = true;
    xAxisLabel: string = '';
    yAxisLabel: string = '';
    //yAxisLabel: string = 'Sentiments';
    legendPosition: string = 'below';
    timeline: boolean = false;
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
        console.log("Tweetiment Lines Component");

        this.tweetimentLines = this.data.result[4].graphic[0].sentiment;
        console.log("Tweetiment Lines", this.tweetimentLines);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
