import { Component, Input, OnInit } from '@angular/core';

@Component({
    selector: 'ngx-profile-data',
    styleUrls: ['./profile-data.component.scss'],
    templateUrl: './profile-data.component.html',
})
export class ProfileDataComponent implements OnInit {
    @Input() private name: any;
    @Input() private usern: any;
    @Input() private organization: any;
    @Input() private location: any;
    @Input() private geo: any;
    @Input() private emails: any;
    @Input() private phone: any;
    @Input() private url: any;
    @Input() private bio: any;

    constructor() {}

    ngOnInit() {
        console.log("Profile Data Component");
    }
}
