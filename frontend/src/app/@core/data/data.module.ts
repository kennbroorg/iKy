import { NgModule, ModuleWithProviders } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DataGatherInfoService } from './data-gather-info.service';
import { LayoutService } from './layout.service';
import { StateService } from './state.service';

const SERVICES = [
  DataGatherInfoService,
  LayoutService,
  StateService,
];

@NgModule({
  imports: [
    CommonModule,
  ],
  providers: [
    ...SERVICES,
  ],
})
export class DataModule {
  static forRoot(): ModuleWithProviders {
    return <ModuleWithProviders>{
      ngModule: DataModule,
      providers: [
        ...SERVICES,
      ],
    };
  }
}
