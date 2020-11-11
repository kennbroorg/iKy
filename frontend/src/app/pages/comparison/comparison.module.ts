import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { ChartModule } from 'angular2-chartjs';
import {
    NbListModule,
    NbUserModule,
    NbButtonModule,
    NbCardModule,
    NbIconModule,
    NbTabsetModule,
    NbDialogModule,
    NbTooltipModule,
    NbInputModule,
    NbTreeGridModule,
    NbAccordionModule,
    NbWindowModule,
    NbDatepickerModule,
} from '@nebular/theme';

import { Ng2SmartTableModule } from 'ng2-smart-table';

import { NbBadgeModule } from '@nebular/theme';
import { TreeModule } from 'angular-tree-component';

import { ThemeModule } from '../../@theme/theme.module';
import { ComparisonComponent } from './comparison.component';

import { SharedModule } from '../shared/shared.module';

// Twitter
import { TwitterCSocialComponent } from './twitterC/twitterC-social/twitter-social.component';
import { TwitterCListComponent } from './twitterC/twitterC-list/twitter-list.component';
import { TwitterCPopularityComponent } from './twitterC/twitterC-popularity/twitter-popularity.component';
import { TwitterCApprovalComponent } from './twitterC/twitterC-approval/twitter-approval.component';
import { TwitterCResumeComponent } from './twitterC/twitterC-resume/twitter-resume.component';
import { TwitterCHashtagComponent } from './twitterC/twitterC-hashtag/twitter-hashtag.component';
import { TwitterCUsersComponent } from './twitterC/twitterC-users/twitter-users.component';
import { TwitterCHourComponent } from './twitterC/twitterC-hour/twitter-hour.component';
import { TwitterCWeekComponent } from './twitterC/twitterC-week/twitter-week.component';
import { StatusCardComponent } from './twitterC/status-card/status-card.component';

@NgModule({
  imports: [
    ThemeModule,
    NgxEchartsModule,
    NgxChartsModule,
    ChartModule,
    NbTabsetModule,
    NbIconModule,
    NbButtonModule,
    NbListModule,
    NbUserModule,
    NbBadgeModule,
    TreeModule,
    NbCardModule,
    NbTooltipModule,
    NbInputModule,
    NbTreeGridModule,
    Ng2SmartTableModule,
    NbAccordionModule,
    SharedModule,
    NbDatepickerModule,
    NbDialogModule.forChild(),
    NbWindowModule.forChild(),
  ],
  declarations: [
    ComparisonComponent,
    TwitterCSocialComponent,
    TwitterCListComponent,
    TwitterCPopularityComponent,
    TwitterCApprovalComponent,
    TwitterCResumeComponent,
    TwitterCHashtagComponent,
    TwitterCHourComponent,
    TwitterCWeekComponent,
    TwitterCUsersComponent,
    StatusCardComponent,
  ],
})
export class ComparisonModule { }
