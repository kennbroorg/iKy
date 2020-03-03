import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';

import { NbBadgeModule, NbCardModule, NbButtonModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { ProfileComponent } from './profile.component';

import { ProfilePhotosComponent } from './profile-photos/profile-photos.component';
import { ProfileDataComponent } from './profile-data/profile-data.component';
import { ProfileSocialComponent } from './profile-social/profile-social.component';

import { SharedModule } from '../shared/shared.module';

@NgModule({
  imports: [
    ThemeModule,
    NgxEchartsModule,
    NbBadgeModule,
    NbCardModule,
    NbButtonModule,
    SharedModule,
  ],
  declarations: [
    ProfileComponent,
    ProfilePhotosComponent,
    ProfileDataComponent,
    ProfileSocialComponent,
  ],
})
export class ProfileModule { }
