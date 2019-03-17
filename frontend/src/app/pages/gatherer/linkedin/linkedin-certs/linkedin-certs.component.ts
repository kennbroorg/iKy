import { Component, OnInit, OnDestroy, Input, ViewChild, ElementRef } from '@angular/core';
import { NbThemeService, NbMediaBreakpoint, NbMediaBreakpointsService } from '@nebular/theme';

@Component({
    selector: 'ngx-linkedin-certs',
    styleUrls: ['./linkedin-certs.component.scss'],
    templateUrl: './linkedin-certs.component.html',
})
export class LinkedinCertsComponent implements OnInit, OnDestroy {

    contacts: any[];
    recent: any[];
    breakpoint: NbMediaBreakpoint;
    breakpoints: any;
    themeSubscription: any;

    @Input() private data: any;
    private linkedinCerts : any;
    private linkedinPositions : any;
    private validation : any;

    constructor(private themeService: NbThemeService,
                private breakpointService: NbMediaBreakpointsService) {

        this.breakpoints = this.breakpointService.getBreakpointsMap();
        this.themeSubscription = this.themeService.onMediaQueryChange()
            .subscribe(([oldValue, newValue]) => {
                this.breakpoint = newValue;
            });
    }

    ngOnInit() {

        console.log("Linkedin Certs Component");
        this.linkedinCerts = this.data.result[4].graphic[2].certificationView;
        this.linkedinPositions = this.data.result[4].graphic[3].positionGroupView;

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
    }

    ngOnDestroy() {
      this.themeSubscription.unsubscribe();
    }
}
