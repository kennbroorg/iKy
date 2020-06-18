import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-instagram-tagged',
    templateUrl: './instagram-tagged.component.html',
    styleUrls: ['./instagram-tagged.component.scss']
})
export class InstagramTaggedComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardInstagramTagged', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private instagramTagged : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.instagramTagged = this.data.result[4].graphic[5].tagged;
        console.log("Instagram Tagged Component");
        console.log(this.instagramTagged);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
