import { NgModule } from '@angular/core';

import { NgxChartsModule } from '@swimlane/ngx-charts';

import { ThemeModule } from '../../@theme/theme.module';
import { PrincipalComponent } from './principal.component';
import { LogoIkyComponent } from './logo-iky/logo-iky.component';

@NgModule({
  imports: [
    ThemeModule,
    NgxChartsModule, 
  ],
  declarations: [
    PrincipalComponent,
    LogoIkyComponent,
  ],
})
export class PrincipalModule { }
