import { ChangeDetectionStrategy, Component, OnInit, OnDestroy } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import {Router} from '@angular/router'

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
    private datas: any;
    public  gathered: any = [];
    public  searchSubs: any;
    public  profile: any = [];
    public  name: any = [];
    public  usern: any = [];
    public  location: any = [];
    public  url: any = [];
    public  geo: any = [];
    public  bio: any = [];
    public  gender: any = [];
    public  social: any = [];
    public  photo: any = [];
    public  phone: any = [];
    public  emails: any = [];
    public  organization: any = [];
    public  presence: any = [];
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
            console.log("Global data initialize");

            console.log("Search", data);
            this.gathered = this.dataGatherService.validateEmail(data.term);
            this.router.navigate(['/pages/gatherer'])
        })

        console.log("ProfileComponent ngOnInit")

        // Check global data
        this.gathered = this.dataGatherService.pullGather();

        // Mail from search
        // TODO: Add mail from search
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
                          if (this.gathered[i][j][k][l][p][q] != null) {
                              this.name.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          };
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
                        case 'username':
                          this.usern.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'location':
                          this.location.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'url':
                          this.url.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'bio':
                          this.bio.push(this.gathered[i][j][k][l][p][q]);
                          break;
                        case 'email':
                          this.emails.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'phone':
                          this.phone.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'geo':
                          this.geo.push(this.gathered[i][j][k][l][p][q]);
                          break;
                        case 'organization':
                          if (Array.isArray(this.gathered[i][j][k][l][p][q])) {
                              for (let r in this.gathered[i][j][k][l][p][q]) {
                                  this.organization.push({"label" : this.gathered[i][j][k][l][p][q][r]['name'], "source" : i});
                              }

                          } else {
                              this.organization.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          }    
                          break;
                        case 'gender':
                          this.gender.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'presence':
                          this.presence.push({"children" : this.gathered[i][j][k][l][p][q][0]['children'],
                                              "name" : this.gathered[i][j][k][l][p][q][0]['name']
                          });
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
        console.log('name', this.name);
        console.log('usern', this.usern);
        console.log('location', this.location);
        console.log('url', this.url);
        console.log('bio', this.bio);
        console.log('geo', this.geo);
        console.log('gender', this.gender);
        console.log('social', this.social);
        console.log('photo', this.photo);
        console.log('orgnization', this.organization);
        console.log('phone', this.phone);
        console.log('email', this.email);
        console.log('presence', this.presence);
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }

    toggleFlipViewAndSearch(email: string, username: string, 
                            twitter: string, instagram: string, 
                            linkedin: string, github: string, 
                            tiktok: string, tinder: string, 
                            venmo: string, reddit: string, 
                            spotify: string, twitch: string, 
                            keybase: string, mastodon: string) {
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
        console.log('twitch', twitch);
        console.log('keybase', keybase);
        console.log('mastodon', mastodon);

        this.flipped = !this.flipped;

        // JSON datas
        this.datas = {email: email,
            username: username,
            twitter: twitter,
            instagram: instagram,
            linkedin: linkedin,
            github: github,
            // tiktok: tiktok,
            // tinder: tinder,
            tiktok: '',
            tinder: '',
            venmo: venmo,
            reddit: reddit,
            spotify: spotify,
            twitch: twitch,
            keybase: keybase,
            mastodon: mastodon,
        };

        this.gathered = this.dataGatherService.initialize();
        console.log('Global data initialize (Advance Gatherer)', this.gathered);

        this.gathered = this.dataGatherService.gathererInfoAdvance(this.datas);
        this.gathered = this.dataGatherService.pullGather();

    }

    toggleFlipView() {
        this.flipped = !this.flipped;
    }

}
