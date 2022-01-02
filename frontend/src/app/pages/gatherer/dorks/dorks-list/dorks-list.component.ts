import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-list',
    templateUrl: './dorks-list.component.html',
    styleUrls: ['./dorks-list.component.scss'],
})
export class DorksListComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardDorksList', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksList : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksList = this.data.result[4].graphic[4].searches;
        console.log("Dorks List Component");
        console.log("Dorks List data", this.dorksList);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
