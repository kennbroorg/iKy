import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-week',
    templateUrl: './instagram-week.component.html',
    styleUrls: ['./instagram-week.component.scss']
})
export class InstagramWeekComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardInstagramWeek', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramWeek : any;

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
        console.log("Instagram Week Component");

        this.instagramWeek = this.data.result[4].graphic[7].week;
        console.log("InstagramWeek", this.instagramWeek);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
