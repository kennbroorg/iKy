import { Component, Input } from '@angular/core';
import { NbDialogRef } from '@nebular/theme';

@Component({
    selector: 'ngx-modal-dialog',
    templateUrl: 'modal-dialog.component.html',
    styleUrls: ['modal-dialog.component.scss'],
})
export class ModalDialogComponent {
    @Input() title: string;
    @Input() text: string;
  
    constructor(protected ref: NbDialogRef<ModalDialogComponent>) {}
  
}
