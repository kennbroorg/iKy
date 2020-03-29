import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-darkpass-list',
    templateUrl: './darkpass-list.component.html',
    styleUrls: ['./darkpass-list.component.scss'],
})
export class DarkpassListComponent implements OnInit, AfterViewInit {

    // contacts: any[];
    // recent: any[];

    @ViewChild('nbCardDarkpassList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private darkpassList : any;
    private statusFull : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log("Darkpass List Component");
        this.darkpassList = this.data.result[4].graphic[0].darkpass;
        try {
             this.statusFull = this.data.result[3].raw['status'];
        }
        catch (e) {
             this.statusFull = "";
        }
        console.log("Darkpass Status: ", this.data.result[3].raw);
        console.log("Darkpass Status: ", this.statusFull);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
