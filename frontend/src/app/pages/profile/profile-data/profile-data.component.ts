import { Component, Input, OnInit } from '@angular/core';

@Component({
    selector: 'ngx-profile-data',
    styleUrls: ['./profile-data.component.scss'],
    templateUrl: './profile-data.component.html',
})
export class ProfileDataComponent implements OnInit {
    @Input() private name: any;
    @Input() private organization: any;
    @Input() private location: any;

    constructor() {}

    ngOnInit() {
        console.log("Profile Data Component");
    }
}
