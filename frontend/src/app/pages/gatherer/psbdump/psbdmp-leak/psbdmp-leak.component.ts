import { Component, OnInit, Input, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-psbdmp-leak',
    templateUrl: './psbdmp-leak.component.html',
    styleUrls: ['./psbdmp-leak.component.scss'],
})
export class PsbDmpLeakComponent implements OnInit {
    @Input() private data: any;
    private psbdmpLeak: any;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.psbdmpLeak = this.data.result[4].graphic[1].dword;
        console.log('PsbDmp  Component');
        console.log(this.psbdmpLeak);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
