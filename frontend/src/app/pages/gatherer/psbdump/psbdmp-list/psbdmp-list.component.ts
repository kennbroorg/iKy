import { Component, OnInit, Input, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-psbdmp-list',
    templateUrl: './psbdmp-list.component.html',
    styleUrls: ['./psbdmp-list.component.scss'],
})
export class PsbDmpListComponent implements OnInit {

    contacts: any[];
    recent: any[];

    @Input() private data: any;
    private psbdmpList: any;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log('PsbDmp List Component');
        this.psbdmpList = this.data.result[4].graphic[0].dlist;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
