import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-socialscan-user',
    templateUrl: './socialscan-user.component.html',
    styleUrls: ['./socialscan-user.component.scss']
})
export class SocialscanUserComponent implements OnInit {
    @ViewChild('nbCardSocialscanUser', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private socialscanUser : any;
    private validation : any;
  
    private card: any;
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Socialscan User Component");
        this.socialscanUser = this.data.result[4].graphic[1].social_user;
        console.log("Socialscan User data: ", this.socialscanUser);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
