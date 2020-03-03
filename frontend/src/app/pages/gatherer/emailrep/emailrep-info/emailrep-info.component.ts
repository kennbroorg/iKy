import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-emailrep-info',
    templateUrl: './emailrep-info.component.html',
    styleUrls: ['./emailrep-info.component.scss']
})
export class EmailrepInfoComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: true }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private emailrepInfo : any;
    private statusFull : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("EmailRep Info Component");
        this.emailrepInfo = this.data.result[4].graphic[0].details;
        this.validation = this.data.result[2].validation;
        try {
             this.statusFull = this.data.result[3].raw[0].title;
        }
        catch (e) {
             this.statusFull = "";
        }
        console.log("Emailrep Status: ", this.statusFull);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
