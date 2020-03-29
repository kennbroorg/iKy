import { Component, OnInit, Input, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-venmo-friends',
    templateUrl: './venmo-friends.component.html',
    styleUrls: ['./venmo-friends.component.scss']
})
export class VenmoFriendsComponent implements OnInit {
    @ViewChild('nbCardVenmoFriends', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private venmoFriends : any;
    private validation : any;

    constructor(private dialogService: NbDialogService) {}
  
    ngOnInit() {
        console.log("Venmo Friends Component");
        this.venmoFriends = this.data.result[4].graphic[1].friends;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
