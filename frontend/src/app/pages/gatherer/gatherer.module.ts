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
    NbPopoverModule,
    NbSpinnerModule,
    NbTabsetModule,
    NbDialogModule,
    NbTooltipModule,
    NbInputModule,
    NbTreeGridModule,
    NbAccordionModule,
    NbWindowModule } from '@nebular/theme';

import { Ng2SmartTableModule } from 'ng2-smart-table';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';

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
import { TwitterTimelineComponent } from './twitter/twitter-timeline/twitter-timeline.component';

import { LinkedinGraphsComponent } from './linkedin/linkedin-graphs/linkedin-graphs.component';
import { LinkedinBubbleComponent } from './linkedin/linkedin-bubble/linkedin-bubble.component';
import { LinkedinCertsComponent } from './linkedin/linkedin-certs/linkedin-certs.component';
import { LinkedinPosComponent } from './linkedin/linkedin-pos/linkedin-pos.component';

import { KeybaseGraphComponent } from './keybase/keybase-graph/keybase-graph.component';
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
import { InstagramListComponent } from './instagram/instagram-list/instagram-list.component';

import { SearchHashtagComponent } from './search/search-hashtag/search-hashtag.component';
import { SearchMentionsComponent } from './search/search-mention/search-mentions.component';
import { SearchNamesComponent } from './search/search-names/search-names.component';
import { SearchUsernamesComponent } from './search/search-usernames/search-usernames.component';
import { SearchSocialComponent } from './search/search-social/search-social.component';
import { SearchSearchesComponent } from './search/search-searches/search-searches.component';
import { SearchListComponent } from './search/search-list/search-list.component';
import { SearchRawListComponent } from './search/search-list-raw/search-list-raw.component';
import { SearchEmailComponent } from './search/search-email/search-email.component';

import { DorksNamesComponent } from './dorks/dorks-names/dorks-names.component';
import { DorksSocialComponent } from './dorks/dorks-social/dorks-social.component';
import { DorksUsernamesComponent } from './dorks/dorks-usernames/dorks-usernames.component';
import { DorksSearchesComponent } from './dorks/dorks-searches/dorks-searches.component';
import { DorksListComponent } from './dorks/dorks-list/dorks-list.component';
import { DorksRawListComponent } from './dorks/dorks-list-raw/dorks-list-raw.component';
import { DorksMentionsComponent } from './dorks/dorks-mention/dorks-mentions.component';
import { DorksHashtagComponent } from './dorks/dorks-hashtag/dorks-hashtag.component';
import { DorksEmailComponent } from './dorks/dorks-email/dorks-email.component';

import { TiktokGraphsComponent } from './tiktok/tiktok-graphs/tiktok-graphs.component';

import { SherlockGraphComponent } from './sherlock/sherlock-graphs/sherlock-graphs.component';
import { SherlockListComponent } from './sherlock/sherlock-list/sherlock-list.component';

import { HoleheGraphComponent } from './holehe/holehe-graphs/holehe-graphs.component';
import { HoleheListComponent } from './holehe/holehe-list/holehe-list.component';

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

import { SpotifySocialComponent } from './spotify/spotify-social/spotify-social.component';
import { SpotifyPlaylistsComponent } from './spotify/spotify-playlists/spotify-playlists.component';
import { SpotifyAutorsComponent } from './spotify/spotify-autors/spotify-autors.component';
import { SpotifyLangComponent } from './spotify/spotify-lang/spotify-lang.component';
import { SpotifyWordsComponent } from './spotify/spotify-words/spotify-words.component';

import { TwitchSocialComponent } from './twitch/twitch-social/twitch-social.component';
import { TwitchListComponent } from './twitch/twitch-list/twitch-list.component';
import { TwitchTimelineComponent } from './twitch/twitch-timeline/twitch-timeline.component';
import { TwitchHourComponent } from './twitch/twitch-hour/twitch-hour.component';
import { TwitchWeekComponent } from './twitch/twitch-week/twitch-week.component';
import { TwitchDurationComponent } from './twitch/twitch-duration/twitch-duration.component';

import { MastodonGraphComponent } from './mastodon/mastodon-graph/mastodon-graph.component';
import { MastodonSocialComponent } from './mastodon/mastodon-social/mastodon-social.component';
import { MastodonListComponent } from './mastodon/mastodon-list/mastodon-list.component';

// import { FsIconComponent, TaskexecComponent } from './taskexec/taskexec.component';
import { TaskexecComponent } from './taskexec/taskexec.component';

import { SharedModule } from '../shared/shared.module';
import { ErrorGraphsComponent } from './error/error-graphs.component';

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
    NbPopoverModule,
    NbTooltipModule,
    NbInputModule,
    NbTreeGridModule,
    Ng2SmartTableModule,
    NgxDatatableModule,
    NbAccordionModule,
    SharedModule,
    LeafletModule,
    NbDialogModule.forChild(),
    NbWindowModule.forChild(),
  ],
  declarations: [
    GathererComponent,
    ErrorGraphsComponent,
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
    TwitterTimelineComponent,
    LinkedinGraphsComponent,
    LinkedinBubbleComponent,
    LinkedinCertsComponent,
    LinkedinPosComponent,
    KeybaseGraphComponent,
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
    InstagramListComponent,
    SearchHashtagComponent,
    SearchMentionsComponent,
    SearchNamesComponent,
    SearchUsernamesComponent,
    SearchSocialComponent,
    SearchSearchesComponent,
    SearchListComponent,
    SearchRawListComponent,
    SearchEmailComponent,
    DorksNamesComponent,
    DorksSocialComponent,
    DorksUsernamesComponent,
    DorksListComponent,
    DorksRawListComponent,
    DorksMentionsComponent,
    DorksHashtagComponent,
    DorksEmailComponent,
    DorksSearchesComponent,
    TiktokGraphsComponent,
    SkypeComponent,
    TaskexecComponent,
    // FsIconComponent,
    SherlockGraphComponent,
    SherlockListComponent,
    HoleheGraphComponent,
    HoleheListComponent,
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
    SpotifySocialComponent,
    SpotifyPlaylistsComponent,
    SpotifyAutorsComponent,
    SpotifyLangComponent,
    SpotifyWordsComponent,
    TwitchSocialComponent,
    TwitchListComponent,
    TwitchTimelineComponent,
    TwitchHourComponent,
    TwitchWeekComponent,
    TwitchDurationComponent,
    MastodonGraphComponent,
    MastodonSocialComponent,
    MastodonListComponent,
  ],
  providers: [
    InstagramMapService,
  ],
})
export class GathererModule { }
