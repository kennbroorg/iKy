import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-resume',
    templateUrl: './twitter-resume.component.html',
    styleUrls: ['./twitter-resume.component.scss']
})
export class TwitterResumeComponent implements OnInit, AfterViewInit {

    @ViewChild('nbCardTwitterResume', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterResume : any;

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

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.card = this.cardContainer.nativeElement;
    }

    ngAfterViewInit() {
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.clientHeight;
        console.log("Twitter Resume Component");

        this.twitterResume = this.data.result[4].graphic[1].resume.children.map(this.arrayAdecuate);
        console.log("Twitter Resume data", this.twitterResume);
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['total']) {
            array[index].value = array[index]['total'];
            delete array[index].total;  
        }
        return item;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
