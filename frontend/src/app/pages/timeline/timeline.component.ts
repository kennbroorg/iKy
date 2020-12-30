import { ChangeDetectionStrategy, Component, OnInit, OnDestroy } from '@angular/core';
// import { NbThemeService } from '@nebular/theme';
import {Router} from '@angular/router';

// Search
import { NbSearchService } from '@nebular/theme';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

@Component({
    selector: 'ngx-timeline',
    styleUrls: ['./timeline.component.scss'],
    templateUrl: './timeline.component.html',
    changeDetection: ChangeDetectionStrategy.Default,
})

export class TimelineComponent implements OnInit {
    // private email: string;
    private datas: any;
    public  gathered: any = [];
    public  searchSubs: any;
    public  timeline: any = [];
    public  flipped = false;

    constructor(private router: Router,
                private searchService: NbSearchService,
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log('Global data initialize');

            console.log('Search', data);
            this.gathered = this.dataGatherService.validateEmail(data.term);
            this.router.navigate(['/pages/gatherer']);
        });
        console.log('TimelineComponent ngOnInit');

        // Check global data
        this.gathered = this.dataGatherService.pullGather();

        for (const i in this.gathered) {
          for (const j in this.gathered[i]) {
            for (const k in this.gathered[i][j]) {
              for (const l in this.gathered[i][j][k]) {
                if (l === 'timeline') {
                  for (const t in this.gathered[i][j][k][l]) {
                    this.timeline.push(this.gathered[i][j][k][l][t]);
                  }
                }
              }
            }
          }
        }

        // TODO : Normalize dates

        this.timeline.sort(function(a, b){
            const dateA = a.date.toLowerCase(), dateB = b.date.toLowerCase();
            if (dateA > dateB) // sort string ascending
                return -1;
            if (dateA < dateB)
                return 1;
            return 0;
        });
    }

    toggleFlipViewAndSearch(email, username, twitter, instagram, linkedin, github, tiktok, tinder, venmo, reddit, spotify) {
        console.log('Advance Search');
        console.log('email', email);
        console.log('username', username);
        console.log('twitter', twitter);
        console.log('instagram', instagram);
        console.log('linkedin', linkedin);
        console.log('github', github);
        console.log('tiktok', tiktok);
        console.log('tinder', tinder);
        console.log('venmo', venmo);
        console.log('reddit', reddit);
        console.log('spotify', spotify);

        this.flipped = !this.flipped;

        // JSON datas
        this.datas = {email: email,
            username: username,
            twitter: twitter,
            instagram: instagram,
            linkedin: linkedin,
            github: github,
            tiktok: tiktok,
            tinder: tinder,
            venmo: venmo,
            reddit: reddit,
            spotify: spotify,
        };

        this.gathered = this.dataGatherService.initialize();
        console.log('Global data initialize (Advance Gatherer)', this.gathered);

        this.gathered = this.dataGatherService.gathererInfoAdvance(this.datas);
        this.gathered = this.dataGatherService.pullGather();

        this.router.navigate(['/pages/gatherer']);

    }

    toggleFlipView() {
        this.flipped = !this.flipped;
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }

}
