import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { ChartModule } from 'angular2-chartjs';

import { NbBadgeModule, NbCardModule } from '@nebular/theme';
import { TreeModule } from 'angular-tree-component';

import { ThemeModule } from '../../@theme/theme.module';
import { GathererComponent } from './gatherer.component';

import { ValidationFilterComponent } from './validation/validation-filter.component';

import { GithubGraphsComponent } from './github/github-graphs/github-graphs.component';
import { GithubCalendarComponent } from './github/github-calendar/github-calendar.component';

import { FullcontactGraphsComponent } from './fullcontact/fullcontact-graphs/fullcontact-graphs.component';
import { FullcontactCloudComponent } from './fullcontact/fullcontact-cloud/fullcontact-cloud.component';
import { FullcontactScrambleComponent } from './fullcontact/fullcontact-scramble/fullcontact-scramble.component';

import { TwitterPopularityComponent } from './twitter/twitter-popularity/twitter-popularity.component';
import { TwitterApprovalComponent } from './twitter/twitter-approval/twitter-approval.component';
import { TwitterResumeComponent } from './twitter/twitter-resume/twitter-resume.component';

import { LinkedinGraphsComponent } from './linkedin/linkedin-graphs/linkedin-graphs.component';
import { LinkedinBubbleComponent } from './linkedin/linkedin-bubble/linkedin-bubble.component';
import { LinkedinCertsComponent } from './linkedin/linkedin-certs/linkedin-certs.component';

import { KeybaseSocialComponent } from './keybase/keybase-social/keybase-social.component';
import { KeybaseDevicesComponent } from './keybase/keybase-devices/keybase-devices.component';

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
  ],
  declarations: [
    GathererComponent,
    ValidationFilterComponent,
    GithubGraphsComponent,
    GithubCalendarComponent,
    FullcontactGraphsComponent,
    FullcontactCloudComponent,
    FullcontactScrambleComponent,
    TwitterPopularityComponent,
    TwitterApprovalComponent,
    TwitterResumeComponent,
    LinkedinGraphsComponent,
    LinkedinBubbleComponent,
    LinkedinCertsComponent,
    KeybaseSocialComponent,
    KeybaseDevicesComponent,
  ],
})
export class GathererModule { }
