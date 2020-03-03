import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-socialscan-email',
    templateUrl: './socialscan-email.component.html',
    styleUrls: ['./socialscan-email.component.scss']
})
export class SocialscanEmailComponent implements OnInit {
    @ViewChild('nbCardSocialscanEmail', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private socialscanEmail : any;
    private validation : any;
  
    private card: any;
  
    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Socialscan Email Component");
        this.socialscanEmail = this.data.result[4].graphic[0].social_email;
        console.log("Socialscan Email data: ", this.socialscanEmail);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
