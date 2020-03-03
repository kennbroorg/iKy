// import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
// import { BubbleComponent } from '../../../shared/bubble/bubble.component';
import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-linkedin-bubble',
    templateUrl: './linkedin-bubble.component.html',
    styleUrls: ['./linkedin-bubble.component.scss']
})
export class LinkedinBubbleComponent implements OnInit {
    @ViewChild('nbCardLinkedinBubble', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private linkedinBubble : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Linkedin Bubble Component");
        this.linkedinBubble = this.data.result[4].graphic[1].skills.children;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
