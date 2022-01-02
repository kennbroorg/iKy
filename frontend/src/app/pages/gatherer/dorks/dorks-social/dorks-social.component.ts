import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-social',
    templateUrl: './dorks-social.component.html',
    styleUrls: ['./dorks-social.component.scss']
})
export class DorksSocialComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardDorksSocial', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksSocial : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksSocial = this.data.result[4].graphic[2].social;
        console.log("Dorks Social Component");
        console.log("Social data", this.dorksSocial);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
