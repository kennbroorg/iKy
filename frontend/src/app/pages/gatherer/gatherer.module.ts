import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { ChartModule } from 'angular2-chartjs';
import { NbDialogModule, NbWindowModule } from '@nebular/theme';

import { NbBadgeModule, NbCardModule } from '@nebular/theme';
import { TreeModule } from 'angular-tree-component';

import { ThemeModule } from '../../@theme/theme.module';
import { GathererComponent } from './gatherer.component';

import { LeafletModule } from '@asymmetrik/ngx-leaflet';

import { ValidationFilterComponent } from './validation/validation-filter.component';

import { GithubGraphsComponent } from './github/github-graphs/github-graphs.component';
import { GithubCalendarComponent } from './github/github-calendar/github-calendar.component';

import { FullcontactGraphsComponent } from './fullcontact/fullcontact-graphs/fullcontact-graphs.component';
import { FullcontactCloudComponent } from './fullcontact/fullcontact-cloud/fullcontact-cloud.component';
import { FullcontactScrambleComponent } from './fullcontact/fullcontact-scramble/fullcontact-scramble.component';

import { TwitterListComponent } from './twitter/twitter-list/twitter-list.component';
import { TwitterPopularityComponent } from './twitter/twitter-popularity/twitter-popularity.component';
import { TwitterApprovalComponent } from './twitter/twitter-approval/twitter-approval.component';
import { TwitterResumeComponent } from './twitter/twitter-resume/twitter-resume.component';
import { TwitterHashtagComponent } from './twitter/twitter-hashtag/twitter-hashtag.component';
import { TwitterUsersComponent } from './twitter/twitter-users/twitter-users.component';

import { LinkedinGraphsComponent } from './linkedin/linkedin-graphs/linkedin-graphs.component';
import { LinkedinBubbleComponent } from './linkedin/linkedin-bubble/linkedin-bubble.component';
import { LinkedinCertsComponent } from './linkedin/linkedin-certs/linkedin-certs.component';

import { KeybaseSocialComponent } from './keybase/keybase-social/keybase-social.component';
import { KeybaseDevicesComponent } from './keybase/keybase-devices/keybase-devices.component';

import { LeakGraphsComponent } from './leak/leak-graphs/leak-graphs.component';

import { EmailrepSocialComponent } from './emailrep/emailrep-social/emailrep-social.component';
import { EmailrepInfoComponent } from './emailrep/emailrep-info/emailrep-info.component';

import { SocialscanEmailComponent } from './socialscan/socialscan-email/socialscan-email.component';
import { SocialscanUserComponent } from './socialscan/socialscan-user/socialscan-user.component';

import { InstagramMapComponent } from './instagram/instagram-map/instagram-map.component';
import { InstagramMapService } from './instagram/instagram-map/instagram-map.service';
import { InstagramGraphsComponent } from './instagram/instagram-graphs/instagram-graphs.component';
import { InstagramPostsComponent } from './instagram/instagram-posts/instagram-posts.component';

import { SharedModule } from '../shared/shared.module';

@NgModule({
  imports: [
    ThemeModule,
    NgxEchartsModule,
    NgxChartsModule, 
    ChartModule,
    NbBadgeModule,
    TreeModule,
    NbCardModule,
    SharedModule,
    LeafletModule,
    NbDialogModule.forChild(),
    NbWindowModule.forChild(),
  ],
  declarations: [
    GathererComponent,
    ValidationFilterComponent,
    GithubGraphsComponent,
    GithubCalendarComponent,
    FullcontactGraphsComponent,
    FullcontactCloudComponent,
    FullcontactScrambleComponent,
    TwitterListComponent,
    TwitterPopularityComponent,
    TwitterApprovalComponent,
    TwitterResumeComponent,
    TwitterHashtagComponent,
    TwitterUsersComponent,
    LinkedinGraphsComponent,
    LinkedinBubbleComponent,
    LinkedinCertsComponent,
    KeybaseSocialComponent,
    KeybaseDevicesComponent,
    LeakGraphsComponent,
    EmailrepInfoComponent,
    EmailrepSocialComponent,
    SocialscanEmailComponent,
    SocialscanUserComponent,
    InstagramGraphsComponent,
    InstagramMapComponent,
    InstagramPostsComponent,
  ],
  providers: [
    InstagramMapService,
  ],
})
export class GathererModule { }
