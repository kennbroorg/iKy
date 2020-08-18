import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-twvsrt',
    templateUrl: './twitter-twvsrt.component.html',
    styleUrls: ['./twitter-twvsrt.component.scss']
})
export class TwitterTwvsrtComponent implements OnInit, AfterViewInit {
    themeSubscription: any;

    @ViewChild('nbCardTwitterTwvsrt', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterTwvsrt : any;

    private card: any;
    private width: number;
    private height: number;

    
    // options
    gradient: boolean = false;
    showLegend: boolean = true;
    showLabels: boolean = true;
    isDoughnut: boolean = false;
    legendPosition: string = 'below';

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

        console.log("Twitter Twvsrt Component");

        this.twitterTwvsrt = this.data.result[4].graphic[11].twvsrt;
        // this.twitterTwvsrt = this.data.result[4].graphic[3].approval.map(this.arrayAdecuate);
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['title']) {
            array[index].name = array[index]['title'];
            delete array[index].title;  
        }
        return item;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
