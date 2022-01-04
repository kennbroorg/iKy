import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-names',
    templateUrl: './dorks-names.component.html',
    styleUrls: ['./dorks-names.component.scss']
})
export class DorksNamesComponent implements OnInit, AfterViewInit {
    @ViewChild('nbCardDorksNames', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksNames : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksNames = this.data.result[4].graphic[0].names;
        console.log("Dorks Names Component");
        console.log("Names data", this.dorksNames);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
