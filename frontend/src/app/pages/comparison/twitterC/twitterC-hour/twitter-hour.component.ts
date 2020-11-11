import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-hour',
    templateUrl: './twitter-hour.component.html',
    styleUrls: ['./twitter-hour.component.scss'],
})
export class TwitterCHourComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterHour', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterHour: any;

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
        this.twitterHour = this.data.result[4].graphic[4].hour;
        console.log('TwitterHour', this.twitterHour);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
