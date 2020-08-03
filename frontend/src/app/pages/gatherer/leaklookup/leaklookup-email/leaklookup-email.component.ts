import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-leaklookup-email',
    templateUrl: './leaklookup-email.component.html',
    styleUrls: ['./leaklookup-email.component.scss'],
})
export class LeaklookupEmailComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardLeaklookupEmail', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private leaklookupEmail : any;
    private statusFull : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log("Leaklookup Email Component");
        this.leaklookupEmail = this.data.result[4].graphic[0].email;
        console.log("Leaklookup Data", this.leaklookupEmail);
        if (this.data.result[3].raw.error == "true" ) {
             this.statusFull = this.data.result[3].raw.message;
        } else {
             this.statusFull = "";
        }
        console.log("Leaklookup Status", this.statusFull);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
