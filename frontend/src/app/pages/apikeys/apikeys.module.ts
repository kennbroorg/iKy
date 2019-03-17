import { NgModule } from '@angular/core';
import { Ng2SmartTableModule } from 'ng2-smart-table';
// import { SmartTableService } from '../../@core/data/smart-table.service';

import { NbBadgeModule, NbCardModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { ApiKeysComponent } from './apikeys.component';

import { NbDialogModule, NbWindowModule } from '@nebular/theme';

@NgModule({
  imports: [
    ThemeModule,
    NbBadgeModule,
    NbCardModule,
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
