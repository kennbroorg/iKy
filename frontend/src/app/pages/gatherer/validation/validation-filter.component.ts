import { Component, Input } from '@angular/core';

@Component({
  selector: 'ngx-validation-filter',
  styleUrls: ['./validation-filter.component.scss'],
  template: `
    <nb-card (click)="on = !on" [ngClass]="{'off': !on}">
      <div class="icon-container">
        <div class="icon {{ type }}">
          <ng-content></ng-content>
        </div>
      </div>

      <div class="details">
        <div class="title">{{ title }}  <span class="status"> - {{ on ? 'ON' : 'OFF' }}</span></div>
        <!-- <div class="status">{{ on ? 'ON' : 'OFF' }}</div> -->
      </div>
    </nb-card>
  `,
})
export class ValidationFilterComponent {

  @Input() title: string;
  @Input() type: string;
  @Input() on = true;
}
