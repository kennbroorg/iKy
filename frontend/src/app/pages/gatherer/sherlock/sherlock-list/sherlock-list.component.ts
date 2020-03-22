import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-sherlock-list',
    templateUrl: './sherlock-list.component.html',
    styleUrls: ['./sherlock-list.component.scss'],
})
export class SherlockListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardSherlockList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private sherlockList : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.sherlockList = this.data.result[4].graphic[1].lists;
        console.log("Sherlock List Component");
        console.log("Sherlock List data", this.sherlockList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
