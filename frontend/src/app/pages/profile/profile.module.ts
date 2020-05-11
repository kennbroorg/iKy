import { NgModule } from '@angular/core';

import { NgxEchartsModule } from 'ngx-echarts';

import { NbBadgeModule, 
         NbCardModule, 
         NbTooltipModule,
         NbButtonModule } from '@nebular/theme';

import { LeafletModule } from '@asymmetrik/ngx-leaflet';

import { ThemeModule } from '../../@theme/theme.module';
import { ProfileComponent } from './profile.component';

import { ProfilePhotosComponent } from './profile-photos/profile-photos.component';
import { ProfileDataComponent } from './profile-data/profile-data.component';
import { ProfileSocialComponent } from './profile-social/profile-social.component';
import { ProfileMapComponent } from './profile-map/profile-map.component';
import { ProfileMapService } from './profile-map/profile-map.service';

import { SharedModule } from '../shared/shared.module';

@NgModule({
  imports: [
    ThemeModule,
    NgxEchartsModule,
    NbBadgeModule,
    NbCardModule,
    NbTooltipModule,
    NbButtonModule,
    LeafletModule,
    SharedModule,
  ],
  declarations: [
    ProfileComponent,
    ProfilePhotosComponent,
    ProfileDataComponent,
    ProfileSocialComponent,
    ProfileMapComponent,
  ],
  providers: [
    ProfileMapService,
  ],
})
export class ProfileModule { }
