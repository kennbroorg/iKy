import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-skype',
    templateUrl: './skype.component.html',
    styleUrls: ['./skype.component.scss']
})
export class SkypeComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: true }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private skype : any;
    private statusFull : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Skype Info Component");
        this.skype = this.data.result[4].graphic[0].details;
        this.validation = this.data.result[2].validation;
        try {
             this.statusFull = this.data.result[3].raw[0].skype;
        }
        catch (e) {
             this.statusFull = "";
        }
        console.log("Skype Status: ", this.statusFull);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
