import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-list',
    templateUrl: './twitter-list.component.html',
    styleUrls: ['./twitter-list.component.scss'],
})
export class TwitterCListComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterList', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    public twitterList: any;

    public card: any;
    public width: number;
    public height: number;
    // options
    legend: boolean = true;
    showLabels: boolean = true;
    animations: boolean = true;
    xAxis: boolean = false;
    // yAxis: boolean = false;
    yAxis: boolean = true;
    showYAxisLabel: boolean = true;
    showXAxisLabel: boolean = true;
    xAxisLabel: string = '';
    // yAxisLabel: string = 'Tweets';
    yAxisLabel: string = '';
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
          '#006064',
      ],
    };

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.card = this.cardContainer.nativeElement;
    }

    ngAfterViewInit() {
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log('Twitter List Component');

        this.twitterList = this.data.result[4].graphic[2].tweetslist;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
