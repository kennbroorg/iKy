import { Component, Input, OnInit } from '@angular/core';
/* import { icon, findIconDefinition } from '@fortawesome/fontawesome-svg-core' */

@Component({
    selector: 'ngx-profile-social',
    styleUrls: ['./profile-social.component.scss'],
    templateUrl: './profile-social.component.html',
})
export class ProfileSocialComponent implements OnInit {
    @Input() private social: any;
    private faUser: any;

    constructor() {}

    ngOnInit() {
        console.log("Profile Social Component");
        this.social = this.getUnique(this.social, "name")
    }

    private getUnique(arr, comp) {

        const unique = arr
            .map(e => e[comp])
        
             // store the keys of the unique objects
            .map((e, i, final) => final.indexOf(e) === i && i)
        
            // eliminate the dead keys & store unique objects
            .filter(e => arr[e]).map(e => arr[e]);
        
            return unique;
    }
}
