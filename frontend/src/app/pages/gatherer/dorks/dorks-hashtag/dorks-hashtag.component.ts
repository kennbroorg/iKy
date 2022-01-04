import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-hashtag',
    templateUrl: './dorks-hashtag.component.html',
    styleUrls: ['./dorks-hashtag.component.scss']
})
export class DorksHashtagComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardDorksHashtag', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksHashtag : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksHashtag = this.data.result[4].graphic[6].hashtags;
        console.log("Dorks Hashtag Component");
        console.log("Dorks data total", this.data);
        console.log("Dorks data", this.dorksHashtag);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
