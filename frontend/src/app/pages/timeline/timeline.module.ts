import { NgModule } from '@angular/core';
import { NbBadgeModule, NbCardModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { TimelineComponent } from './timeline.component';


@NgModule({
  imports: [
    ThemeModule,
    NbBadgeModule,
    NbCardModule,
  ],
  declarations: [
    TimelineComponent,
  ],
})
export class TimelineModule { }
