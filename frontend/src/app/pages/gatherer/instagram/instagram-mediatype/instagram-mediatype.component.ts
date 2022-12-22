import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-mediatype',
    templateUrl: './instagram-mediatype.component.html',
    styleUrls: ['./instagram-mediatype.component.scss']
})
export class InstagramMediatypeComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardInstagramMediatype', { static: true }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramMediatype : any;

    private card: any;
    private width: number;
    private height: number;
    showLegend = true;
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
        console.log("Instagram Mediatype Component");

        this.instagramMediatype = this.data.result[4].graphic[8].mediatype;
        console.warn("Instagram Mediatype Component", this.instagramMediatype);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
