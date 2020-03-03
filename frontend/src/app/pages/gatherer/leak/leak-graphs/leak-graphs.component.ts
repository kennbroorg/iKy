import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-leak-graphs',
    templateUrl: './leak-graphs.component.html',
    styleUrls: ['./leak-graphs.component.scss']
})
export class LeakGraphsComponent implements OnInit {
    @ViewChild('nbCardLeakGraphs', { static: true }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private leakGraphs : any;
  
    private card: any;
    private height: number;
    private width: number;

    private noData: string = "OK";
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Leak Graphs Component");
        this.leakGraphs = this.data.result[4].graphic[0].leaks;
        console.log("Leak data: ", this.leakGraphs);

        this.card = this.nbCardContainer.nativeElement;

        if (this.data.result[3].raw[0].title != null) {
            this.noData = this.data.result[3].raw[0].title;
            console.log("Leak noData: ", this.noData);
        }
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
