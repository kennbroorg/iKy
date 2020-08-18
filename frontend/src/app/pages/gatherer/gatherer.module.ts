import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { ChartModule } from 'angular2-chartjs';
import { 
    NbListModule, 
    NbUserModule, 
    NbActionsModule, 
    NbButtonModule, 
    NbCardModule, 
    NbIconModule, 
    NbSpinnerModule, 
    NbTabsetModule, 
    NbDialogModule, 
    NbTooltipModule,
    NbInputModule,
    NbTreeGridModule,
    NbAccordionModule,
    NbWindowModule } from '@nebular/theme';

import { Ng2SmartTableModule } from 'ng2-smart-table';

import { NbBadgeModule } from '@nebular/theme';
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

import { TwitterSocialComponent } from './twitter/twitter-social/twitter-social.component';
import { TwitterListComponent } from './twitter/twitter-list/twitter-list.component';
import { TwitterPopularityComponent } from './twitter/twitter-popularity/twitter-popularity.component';
import { TwitterApprovalComponent } from './twitter/twitter-approval/twitter-approval.component';
import { TwitterResumeComponent } from './twitter/twitter-resume/twitter-resume.component';
import { TwitterHashtagComponent } from './twitter/twitter-hashtag/twitter-hashtag.component';
import { TwitterUsersComponent } from './twitter/twitter-users/twitter-users.component';
import { TwitterHourComponent } from './twitter/twitter-hour/twitter-hour.component';
import { TwitterWeekComponent } from './twitter/twitter-week/twitter-week.component';
import { TwitterSourceComponent } from './twitter/twitter-source/twitter-source.component';
import { TwitterTwvsrtComponent } from './twitter/twitter-twvsrt/twitter-twvsrt.component';

import { LinkedinGraphsComponent } from './linkedin/linkedin-graphs/linkedin-graphs.component';
import { LinkedinBubbleComponent } from './linkedin/linkedin-bubble/linkedin-bubble.component';
import { LinkedinCertsComponent } from './linkedin/linkedin-certs/linkedin-certs.component';
import { LinkedinPosComponent } from './linkedin/linkedin-pos/linkedin-pos.component';

import { KeybaseSocialComponent } from './keybase/keybase-social/keybase-social.component';
import { KeybaseDevicesComponent } from './keybase/keybase-devices/keybase-devices.component';

import { LeakGraphsComponent } from './leak/leak-graphs/leak-graphs.component';
import { LeaklookupEmailComponent } from './leaklookup/leaklookup-email/leaklookup-email.component';

import { EmailrepSocialComponent } from './emailrep/emailrep-social/emailrep-social.component';
import { EmailrepInfoComponent } from './emailrep/emailrep-info/emailrep-info.component';

import { SocialscanEmailComponent } from './socialscan/socialscan-email/socialscan-email.component';
import { SocialscanUserComponent } from './socialscan/socialscan-user/socialscan-user.component';

import { InstagramMapComponent } from './instagram/instagram-map/instagram-map.component';
import { InstagramMapService } from './instagram/instagram-map/instagram-map.service';
import { InstagramGraphsComponent } from './instagram/instagram-graphs/instagram-graphs.component';
import { InstagramPostsComponent } from './instagram/instagram-posts/instagram-posts.component';
import { InstagramHashtagComponent } from './instagram/instagram-hashtag/instagram-hashtag.component';
import { InstagramMentionComponent } from './instagram/instagram-mention/instagram-mention.component';
import { InstagramTaggedComponent } from './instagram/instagram-tagged/instagram-tagged.component';
import { InstagramHourComponent } from './instagram/instagram-hour/instagram-hour.component';
import { InstagramWeekComponent } from './instagram/instagram-week/instagram-week.component';
import { InstagramMediatypeComponent } from './instagram/instagram-mediatype/instagram-mediatype.component';
import { InstagramPhotosComponent } from './instagram/instagram-photos/instagram-photos.component';

import { SearchHashtagComponent } from './search/search-hashtag/search-hashtag.component';
import { SearchMentionsComponent } from './search/search-mention/search-mentions.component';
import { SearchNamesComponent } from './search/search-names/search-names.component';
import { SearchUsernamesComponent } from './search/search-usernames/search-usernames.component';
import { SearchSocialComponent } from './search/search-social/search-social.component';
import { SearchSearchesComponent } from './search/search-searches/search-searches.component';
import { SearchListComponent } from './search/search-list/search-list.component';

import { TiktokGraphsComponent } from './tiktok/tiktok-graphs/tiktok-graphs.component';

import { SherlockGraphComponent } from './sherlock/sherlock-graphs/sherlock-graphs.component';
import { SherlockListComponent } from './sherlock/sherlock-list/sherlock-list.component';

import { SkypeComponent } from './skype/skype.component';

import { VenmoGraphsComponent } from './venmo/venmo-graphs/venmo-graphs.component';
import { VenmoFriendsComponent } from './venmo/venmo-friends/venmo-friends.component';
import { VenmoTransComponent } from './venmo/venmo-trans/venmo-trans.component';

import { TinderGraphsComponent } from './tinder/tinder-graphs/tinder-graphs.component';

import { DarkpassListComponent } from './darkpass/darkpass-list/darkpass-list.component';

import { TweetimentLinesComponent } from './tweetiment/tweetiment-lines/tweetiment-lines.component';

import { RedditSocialComponent } from './reddit/reddit-social/reddit-social.component';
import { RedditHourComponent } from './reddit/reddit-hour/reddit-hour.component';
import { RedditWeekComponent } from './reddit/reddit-week/reddit-week.component';
import { RedditBubbleComponent } from './reddit/reddit-bubble/reddit-bubble.component';

import { PeopledatalabsSocialComponent } from './peopledatalabs/peopledatalabs-social/peopledatalabs-social.component';
import { PeopledatalabsGraphsComponent } from './peopledatalabs/peopledatalabs-graphs/peopledatalabs-graphs.component';

import { FsIconComponent, TaskexecComponent } from './taskexec/taskexec.component';

import { SharedModule } from '../shared/shared.module';

@NgModule({
  imports: [
    ThemeModule,
    NgxEchartsModule,
    NgxChartsModule, 
    ChartModule,
    NbTabsetModule,
    NbSpinnerModule,
    NbIconModule,
    NbButtonModule,
    NbActionsModule,  
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
    TwitterSocialComponent,
    TwitterListComponent,
    TwitterPopularityComponent,
    TwitterApprovalComponent,
    TwitterResumeComponent,
    TwitterHashtagComponent,
    TwitterHourComponent,
    TwitterWeekComponent,
    TwitterUsersComponent,
    TwitterSourceComponent,
    TwitterTwvsrtComponent,
    LinkedinGraphsComponent,
    LinkedinBubbleComponent,
    LinkedinCertsComponent,
    LinkedinPosComponent,
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
    InstagramHashtagComponent,
    InstagramMentionComponent,
    InstagramTaggedComponent,
    InstagramHourComponent,
    InstagramWeekComponent,
    InstagramMediatypeComponent,
    InstagramPhotosComponent,
    SearchHashtagComponent,
    SearchMentionsComponent,
    SearchNamesComponent,
    SearchUsernamesComponent,
    SearchSocialComponent,
    SearchSearchesComponent,
    SearchListComponent,
    TiktokGraphsComponent,
    SkypeComponent,
    TaskexecComponent,
    FsIconComponent,
    SherlockGraphComponent,
    SherlockListComponent,
    VenmoGraphsComponent,
    VenmoFriendsComponent,
    VenmoTransComponent,
    TinderGraphsComponent,
    DarkpassListComponent,
    TweetimentLinesComponent,
    RedditSocialComponent,
    RedditHourComponent,
    RedditWeekComponent,
    RedditBubbleComponent,
    PeopledatalabsSocialComponent,
    PeopledatalabsGraphsComponent,
    LeaklookupEmailComponent,
  ],
  providers: [
    InstagramMapService,
  ],
})
export class GathererModule { }
