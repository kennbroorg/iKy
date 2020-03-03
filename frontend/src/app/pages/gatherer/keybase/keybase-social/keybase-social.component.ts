import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-keybase-social',
    templateUrl: './keybase-social.component.html',
    styleUrls: ['./keybase-social.component.scss']
})
export class KeybaseSocialComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private keybaseSocial : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Keybase Social Component");
        this.keybaseSocial = this.data.result[4].graphic[0].keysocial;
        this.validation = this.data.result[2].validation;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
