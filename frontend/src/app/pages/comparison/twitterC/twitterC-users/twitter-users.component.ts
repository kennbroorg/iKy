import { Component, OnInit, Input, AfterViewInit, TemplateRef } from '@angular/core';
// import { ViewChild, ElementRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-users',
    templateUrl: './twitter-users.component.html',
    styleUrls: ['./twitter-users.component.scss'],
})
export class TwitterCUsersComponent implements OnInit, AfterViewInit {
    // @ViewChild('nbCardTwitterUsers', { static: false }) private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterUsers: any;

    public card: any;
    public width: number;
    public height: number;

    constructor(private dialogService: NbDialogService) {}

    ngOnInit() {
        this.twitterUsers = this.data.result[4].graphic[1].users;
    }

    ngAfterViewInit() {

        console.log('Twitter Users Component');
        console.log(this.twitterUsers);
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
