import { NgModule } from '@angular/core';
import { NbMenuModule } from '@nebular/theme';
import { NbIconModule } from '@nebular/theme';

import { PagesComponent } from './pages.component';
import { PrincipalModule } from './principal/principal.module';
import { GathererModule } from './gatherer/gatherer.module';
import { ProfileModule } from './profile/profile.module';
import { TimelineModule } from './timeline/timeline.module';
import { ApiKeysModule } from './apikeys/apikeys.module';
import { ComparisonModule } from './comparison/comparison.module';

import { MiscellaneousModule } from './miscellaneous/miscellaneous.module';

import { ThemeModule } from '../@theme/theme.module';
import { PagesRoutingModule } from './pages-routing.module';

import { SharedModule } from './shared/shared.module';

@NgModule({
  imports: [
    PagesRoutingModule,
    ThemeModule,
    NbMenuModule,
    NbIconModule,
    PrincipalModule,
    GathererModule,
    ProfileModule,
    TimelineModule,
    ApiKeysModule,
    MiscellaneousModule,
    SharedModule,
    ComparisonModule,
  ],
  declarations: [
    PagesComponent,
  ],
})
export class PagesModule {
}
