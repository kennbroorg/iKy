import { Component } from '@angular/core';
import { NbIconLibraries } from '@nebular/theme';

import { MENU_ITEMS } from './pages-menu';

@Component({
  selector: 'ngx-pages',
  styleUrls: ['pages.component.scss'],
  template: `
    <ngx-iky-layout>
      <nb-menu [items]="menu"></nb-menu>
      <router-outlet></router-outlet>
    </ngx-iky-layout>
  `,
})
export class PagesComponent {

  menu = MENU_ITEMS;

  constructor(iconsLibrary: NbIconLibraries) {
    iconsLibrary.registerFontPack('font-awesome', { packClass: 'fa', iconClassPrefix: 'fa' });
    iconsLibrary.registerFontPack('fa', { packClass: 'fa', iconClassPrefix: 'fa' });
    iconsLibrary.registerFontPack('fab', { packClass: 'fab', iconClassPrefix: 'fa' });
    iconsLibrary.setDefaultPack('font-awesome'); 
  }

}
