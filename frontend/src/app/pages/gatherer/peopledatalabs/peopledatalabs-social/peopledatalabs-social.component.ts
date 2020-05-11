import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-peopledatalabs-social',
    templateUrl: './peopledatalabs-social.component.html',
    styleUrls: ['./peopledatalabs-social.component.scss']
})
export class PeopledatalabsSocialComponent implements OnInit {
    @ViewChild('nbCardPeopledatalabsSocial', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private peopledatalabsSocial : any;
    private statusFull : any;
    private validation : any;
  
    private card: any;
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Peopledatalabs Social Component");
        this.peopledatalabsSocial = this.data.result[4].graphic[1].social;
        console.log("Peopledatalabs social: ", this.peopledatalabsSocial);
        this.statusFull = this.data.result[3].raw['status'];
        console.log("Peopledatalabs status: ", this.statusFull);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
