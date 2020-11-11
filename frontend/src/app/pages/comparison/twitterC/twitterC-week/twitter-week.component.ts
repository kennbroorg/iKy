import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-week',
    templateUrl: './twitter-week.component.html',
    styleUrls: ['./twitter-week.component.scss'],
})
export class TwitterCWeekComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterWeek', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    public twitterWeek: any;

    public card: any;
    public width: number;
    public height: number;
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
        console.log('Twitter Week Component');

        this.twitterWeek = this.data.result[4].graphic[3].week;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
