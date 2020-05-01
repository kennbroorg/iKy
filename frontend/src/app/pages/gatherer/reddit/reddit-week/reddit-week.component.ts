import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-reddit-week',
    templateUrl: './reddit-week.component.html',
    styleUrls: ['./reddit-week.component.scss']
})
export class RedditWeekComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardRedditWeek', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private redditWeek : any;

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
        console.log("Reddit Week Component");

        this.redditWeek = this.data.result[4].graphic[2].week;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
