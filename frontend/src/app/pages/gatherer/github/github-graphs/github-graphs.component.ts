import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';
import { NbPopoverDirective, NbPosition, NbTrigger } from '@nebular/theme';

@Component({
    selector: 'ngx-github-graphs',
    templateUrl: './github-graphs.component.html',
    styleUrls: ['./github-graphs.component.scss']
})
export class GithubGraphsComponent implements OnInit {
    @ViewChild('nbCardGraphs', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private githubGraphs : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Github Graphs Component");
        this.githubGraphs = this.data.result[4].graphic[0].github;
        this.validation = this.data.result[2].validation;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
