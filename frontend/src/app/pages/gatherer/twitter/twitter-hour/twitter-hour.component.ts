import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-hour',
    templateUrl: './twitter-hour.component.html',
    styleUrls: ['./twitter-hour.component.scss']
})
export class TwitterHourComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardTwitterHour', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterHour : any;

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
        console.log("Twitter Hour Component");
        console.log("Width", this.width);
        console.log("Height", this.height);

        this.twitterHour = this.data.result[4].graphic[8].hour;
        console.log("TwitterHour", this.twitterHour);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
