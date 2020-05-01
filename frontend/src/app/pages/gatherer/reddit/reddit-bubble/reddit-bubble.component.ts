import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-reddit-bubble',
    templateUrl: './reddit-bubble.component.html',
    styleUrls: ['./reddit-bubble.component.scss']
})
export class RedditBubbleComponent implements OnInit {
    @ViewChild('nbCardRedditBubble', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private redditBubble : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Reddit Bubble Component");
        this.redditBubble = this.data.result[4].graphic[3].topics.children;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
