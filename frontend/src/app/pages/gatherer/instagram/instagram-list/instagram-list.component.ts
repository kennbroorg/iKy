import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-list',
    templateUrl: './instagram-list.component.html',
    styleUrls: ['./instagram-list.component.scss'],
})
export class InstagramListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardInstagramList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramList : any;
    // private validation : any;

    // private card: any;
    // private width: number;
    // private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.instagramList = this.data.result[4].graphic[10].postdet;
        console.log("Search List Raw Component");
        console.log("Search List Raw data", this.instagramList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
