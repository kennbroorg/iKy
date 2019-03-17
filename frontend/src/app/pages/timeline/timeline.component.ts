import { ChangeDetectionStrategy, Component, OnInit, OnDestroy } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import {Router} from "@angular/router"

// Search
import { NbSearchService } from '@nebular/theme';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

@Component({
    selector: 'ngx-timeline',
    styleUrls: ['./timeline.component.scss'],
    templateUrl: './timeline.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class TimelineComponent implements OnInit {
    private email: string;
    public  gathered: any = [];
    public  searchSubs: any;
    public  timeline: any = [];

    constructor(private router: Router,
                private searchService: NbSearchService, 
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log("Global data initialize");

            console.log("Search", data);
            this.gathered = this.dataGatherService.validateEmail(data.term); 
            this.router.navigate(['/pages/gatherer'])
        })
        console.log("TimelineComponent ngOnInit")

        // Check global data
        this.gathered = this.dataGatherService.pullGather();

        for (let i in this.gathered) {
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "timeline") {
                  for (let t in this.gathered[i][j][k][l]) {
                    this.timeline.push(this.gathered[i][j][k][l][t]);
                  }
                }
              }
            }
          }
        }     

        // TODO : Normalize dates

        this.timeline.sort(function(a, b){
            var dateA=a.date.toLowerCase(), dateB=b.date.toLowerCase()
            if (dateA > dateB) //sort string ascending
                return -1 
            if (dateA < dateB)
                return 1
            return 0 
        })
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }
}
