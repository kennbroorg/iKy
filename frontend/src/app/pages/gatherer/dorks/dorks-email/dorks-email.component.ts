import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-email',
    templateUrl: './dorks-email.component.html',
    styleUrls: ['./dorks-email.component.scss']
})
export class DorksEmailComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardDorksEmail', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksEmails : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksEmails = this.data.result[4].graphic[7].emails;
        console.log("Dorks Emails Component");
        console.log("Dorks Emails data", this.dorksEmails);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
