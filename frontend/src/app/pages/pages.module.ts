import { NgModule } from '@angular/core';

import { PagesComponent } from './pages.component';
import { PrincipalModule } from './principal/principal.module';
import { GathererModule } from './gatherer/gatherer.module';
import { ProfileModule } from './profile/profile.module';
import { TimelineModule } from './timeline/timeline.module';
import { ApiKeysModule } from './apikeys/apikeys.module';

import { MiscellaneousModule } from './miscellaneous/miscellaneous.module';

import { PagesRoutingModule } from './pages-routing.module';
import { ThemeModule } from '../@theme/theme.module';

import { SharedModule } from './shared/shared.module';

const PAGES_COMPONENTS = [
    PagesComponent,
];

@NgModule({
  imports: [
    PagesRoutingModule,
    ThemeModule,
    PrincipalModule,
    GathererModule,
    ProfileModule,
    TimelineModule,
    ApiKeysModule,
    MiscellaneousModule,
    SharedModule,
  ],
  declarations: [
    ...PAGES_COMPONENTS,
  ],
}) 
export class PagesModule {
}
