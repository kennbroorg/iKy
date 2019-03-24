import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { NbCardModule } from '@nebular/theme';

import { ModalDialogComponent } from './modal-dialog/modal-dialog.component';
import { BubbleComponent } from './bubble/bubble.component';
import { GraphsComponent } from './graphs/graphs.component';
import { TextCloudComponent } from './text-cloud/text-cloud.component';
import { TextScrambleComponent } from './text-scramble/text-scramble.component';

import { SafePipe } from './pipe/safe.pipe';

 
@NgModule({
  imports: [
    CommonModule,
    NbCardModule,
  ],
  declarations: [
    BubbleComponent,
    GraphsComponent,
    TextCloudComponent,
    TextScrambleComponent,
    SafePipe,
    ModalDialogComponent,
  ],
  exports: [
    CommonModule,
    BubbleComponent,
    GraphsComponent,
    TextCloudComponent,
    TextScrambleComponent,
    SafePipe,
    ModalDialogComponent,
  ],
  entryComponents: [
    ModalDialogComponent,
  ],
})
export class SharedModule { }
