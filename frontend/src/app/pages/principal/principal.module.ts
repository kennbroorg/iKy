import { NgModule } from '@angular/core';

import { NgxChartsModule } from '@swimlane/ngx-charts';
import { NbCardModule } from '@nebular/theme';
import { NbAccordionModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { PrincipalComponent } from './principal.component';

@NgModule({
  imports: [
    ThemeModule,
    NgxChartsModule, 
    NbCardModule,
    NbAccordionModule,
  ],
  declarations: [
    PrincipalComponent,
  ],
})
export class PrincipalModule { }
