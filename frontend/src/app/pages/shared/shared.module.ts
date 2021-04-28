import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { NbCardModule } from '@nebular/theme';

import { ModalDialogComponent } from './modal-dialog/modal-dialog.component';
import { BubbleComponent } from './bubble/bubble.component';
import { SimpleGraphsComponent } from './simple-graphs/simple-graphs.component';
import { GraphsComponent } from './graphs/graphs.component';
import { TextCloudComponent } from './text-cloud/text-cloud.component';
import { TextScrambleComponent } from './text-scramble/text-scramble.component';
import { CircleSocialComponent } from './circle-social/circle-social.component';

import { SafePipe } from './pipe/safe.pipe';

@NgModule({

  imports: [
    CommonModule,
    NbCardModule,
  ],
  declarations: [
    BubbleComponent,
    SimpleGraphsComponent,
    GraphsComponent,
    TextCloudComponent,
    TextScrambleComponent,
    SafePipe,
    ModalDialogComponent,
    CircleSocialComponent,
  ],
  exports: [
    CommonModule,
    BubbleComponent,
    SimpleGraphsComponent,
    GraphsComponent,
    TextCloudComponent,
    TextScrambleComponent,
    SafePipe,
    ModalDialogComponent,
    CircleSocialComponent,
  ],
  entryComponents: [
    ModalDialogComponent,
  ],
})
export class SharedModule { }
