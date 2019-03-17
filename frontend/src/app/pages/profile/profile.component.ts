import { ChangeDetectionStrategy, Component, OnInit, OnDestroy } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import {Router} from "@angular/router"

// Search
import { NbSearchService } from '@nebular/theme';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

@Component({
    selector: 'ngx-profile',
    styleUrls: ['./profile.component.scss'],
    templateUrl: './profile.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

    export class ProfileComponent implements OnInit {
    private email: string;
    public  gathered: any = [];
    public  searchSubs: any;
    public  profile: any = [];
    public  name: any = [];
    public  location: any = [];
    public  gender: any = [];
    public  social: any = [];
    public  photo: any = [];
    public  organization: any = [];

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

        console.log("ProfileComponent ngOnInit")

        // Check global data
        this.gathered = this.dataGatherService.pullGather();

        for (let i in this.gathered) {
            console.log("i", i)
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "profile") {
                  for (let p in this.gathered[i][j][k][l]) {
                    this.profile.push(this.gathered[i][j][k][l][p]);
                    for (let q in this.gathered[i][j][k][l][p]) {
                      switch(q) {
                        case 'name':
                        case 'firstName':
                        case 'lastName':
                          this.name.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'photos':
                          for (let iphoto in this.gathered[i][j][k][l][p][q]) {
                              this.photo.push(this.gathered[i][j][k][l][p][q][iphoto]);
                          };    
                          break;
                        case 'social':
                          for (let isocial in this.gathered[i][j][k][l][p][q]) {
                              this.social.push(this.gathered[i][j][k][l][p][q][isocial]);
                          };    
                          break;
                        case 'location':
                          this.location.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'organization':
                          this.organization.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'gender':
                          this.gender.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        default:
                          // code block
                      }
                    }
                  }
                }
              }
            }
          }
        }     
        // TODO : Analize profile information
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }
}
