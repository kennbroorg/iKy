import { NgModule } from '@angular/core';
import { Ng2SmartTableModule } from 'ng2-smart-table';
// import { SmartTableService } from '../../@core/data/smart-table.service';

import { NbBadgeModule,
         NbButtonModule,
         NbTooltipModule,
         NbCardModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { ApiKeysComponent } from './apikeys.component';

import { NbDialogModule } from '@nebular/theme';
// import { NbDialogModule, NbWindowModule } from '@nebular/theme';

@NgModule({
  imports: [
    ThemeModule,
    NbBadgeModule,
    NbCardModule,
    NbButtonModule,
    NbTooltipModule,
    Ng2SmartTableModule,
    NbDialogModule.forChild(),
  ],
  declarations: [
    ApiKeysComponent,
  ],
    //   providers: [
    //     SmartTableService,
    //   ],
})
export class ApiKeysModule { }
