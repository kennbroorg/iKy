import { Component, Input, OnInit } from '@angular/core';

@Component({
    selector: 'ngx-profile-photos',
    styleUrls: ['./profile-photos.component.scss'],
    templateUrl: './profile-photos.component.html',
})
export class ProfilePhotosComponent implements OnInit {
    @Input() private data: any;
    private selectedPhoto: any;
    private isSingleView: any;

    constructor() {}

    ngOnInit() {
        console.log("Profile Photo Component");
        // this.data = this.getUnique(this.data, "title")
        this.selectedPhoto = this.data[0];
        this.isSingleView = false;
    }

    selectPhoto(photo: any) {
        this.selectedPhoto = photo;
        this.isSingleView = true;
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
