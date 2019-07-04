import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';

@Component({
    selector: 'ngx-github-graphs',
    templateUrl: './github-graphs.component.html',
    styleUrls: ['./github-graphs.component.scss']
})
export class GithubGraphsComponent implements OnInit {
    @ViewChild('nbCardGraphs') private nbCardContainer: ElementRef;
    @Input() private data: any;
    private githubGraphs : any;
    private validation : any;

    constructor() {}

    ngOnInit() {
        console.log("Github Graphs Component");
        this.githubGraphs = this.data.result[4].graphic[0].github;
        this.validation = this.data.result[2].validation;
    }
}
