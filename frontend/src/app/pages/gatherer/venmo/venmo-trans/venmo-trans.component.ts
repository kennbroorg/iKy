import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-venmo-trans',
    templateUrl: './venmo-trans.component.html',
    styleUrls: ['./venmo-trans.component.scss'],
})
export class VenmoTransComponent implements OnInit, AfterViewInit {

    // contacts: any[];
    // recent: any[];

    @ViewChild('nbCardVenmoTrans', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private venmoTrans : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log("Venmo Trans Component");
        this.venmoTrans = this.data.result[4].graphic[2].trans;
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
