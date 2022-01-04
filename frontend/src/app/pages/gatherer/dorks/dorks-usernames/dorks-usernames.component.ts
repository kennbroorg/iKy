import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-usernames',
    templateUrl: './dorks-usernames.component.html',
    styleUrls: ['./dorks-usernames.component.scss']
})
export class DorksUsernamesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardDorksUsernames', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksUsernames : any;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksUsernames = this.data.result[4].graphic[1].username;
        console.log("Dorks UserNames Component");
        console.log("Usernames data", this.dorksUsernames);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
