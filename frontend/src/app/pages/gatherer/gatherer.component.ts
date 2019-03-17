import { ChangeDetectionStrategy, Component, OnInit, OnDestroy } from '@angular/core';
import { NbThemeService } from '@nebular/theme';

// Search
import { NbSearchService } from '@nebular/theme';

// RxJS
import { takeWhile } from 'rxjs/operators' ;
import { Observable } from 'rxjs/Observable';
import { mergeMap } from 'rxjs/operators';

// Toaster 
import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService } from '@nebular/theme';
import { NbToastStatus } from '@nebular/theme/components/toastr/model';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

@Component({
    selector: 'ngx-gatherer',
    styleUrls: ['./gatherer.component.scss'],
    templateUrl: './gatherer.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class GathererComponent implements OnInit {
    public  gathered: any = [];
    public  searchSubs: any;

    constructor(private searchService: NbSearchService, 
        // private dataGatherService: DataGatherService) {
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log("Global data initialize", this.gathered);

            console.log("Search", data);
            this.gathered = this.dataGatherService.validateEmail(data.term); 
        })

        console.log("GathererComponent ngOnInit")
        // Check global data
        this.gathered = this.dataGatherService.pullGather();
        console.log("GathererComponent ngOnInit", this.gathered)
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }
}
