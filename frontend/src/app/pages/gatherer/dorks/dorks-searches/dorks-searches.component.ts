import { Component, OnInit, Input, AfterViewInit, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-dorks-searches',
    templateUrl: './dorks-searches.component.html',
    styleUrls: ['./dorks-searches.component.scss'],
})
export class DorksSearchesComponent implements OnInit, AfterViewInit {
    // @ViewChild('nbCardDorksSearches', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private dorksSearches: any;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.dorksSearches = this.data.result[4].graphic[5].searches;
        console.log('Dorks Searches Component');
        console.log('Dorks data', this.dorksSearches);
    }

    ngAfterViewInit() {
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
