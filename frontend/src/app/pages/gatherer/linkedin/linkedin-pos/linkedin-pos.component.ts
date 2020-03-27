import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, TemplateRef, ViewEncapsulation } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-linkedin-pos',
    templateUrl: './linkedin-pos.component.html',
    styleUrls: ['./linkedin-pos.component.scss'],
})
export class LinkedinPosComponent implements OnInit, AfterViewInit {

    contacts: any[];
    recent: any[];

    @ViewChild('nbCardLinkedinPos', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private linkedinCerts : any;
    private linkedinPositions : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        console.log("Linkedin Certs Component");
        this.linkedinCerts = this.data.result[4].graphic[2].certificationView;
        this.linkedinPositions = this.data.result[4].graphic[3].positionGroupView;
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
