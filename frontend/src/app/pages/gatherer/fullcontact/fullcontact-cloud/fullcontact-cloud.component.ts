import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';

@Component({
    selector: 'ngx-fullcontact-cloud',
    templateUrl: './fullcontact-cloud.component.html',
    styleUrls: ['./fullcontact-cloud.component.scss']
})
export class FullcontactCloudComponent implements OnInit {
    @ViewChild('nbCardFullcontactCloud', { static: false }) private nbCardContainer: ElementRef;
    @Input() private data: any;
    private fullcontactCloud : any;
    private validation : any;
  
    private card: any;
  
    constructor() {}
  
    ngOnInit() {
        console.log("Fullcontact Cloud Component");
        this.fullcontactCloud = this.data.result[4].graphic[4].footprint;
        console.log("Fullcontact data: ", this.fullcontactCloud);
  
        /* Validation */
        switch(this.data.result[2].validation) {
          case 'hard':
            this.validation = 'success';
            break;
          case 'soft':
            this.validation = 'warning';
            break;
          case 'no':
            this.validation = 'danger';
            break;
          default:
            this.validation = 'danger';
        }
        console.log("Validation : ", this.validation);
    }
}
