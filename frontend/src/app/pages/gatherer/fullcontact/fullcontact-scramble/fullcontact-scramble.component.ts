import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { TextScrambleComponent } from '../../../shared/text-scramble/text-scramble.component';

@Component({
    selector: 'ngx-fullcontact-scramble',
    templateUrl: './fullcontact-scramble.component.html',
    styleUrls: ['./fullcontact-scramble.component.scss']
})
export class FullcontactScrambleComponent implements OnInit {
    @ViewChild('nbCardScramble', { static: true }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private fullcontactScramble : any;
    private validation : any;
  
    constructor() {}
  
    ngOnInit() {
        console.log("Fullcontact Scramble Component");
        this.fullcontactScramble = this.data.result[4].graphic[1].bios;
        console.log("Fullcontact data: ", this.fullcontactScramble);
  
    }
}
