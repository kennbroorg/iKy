import { Component } from '@angular/core';

@Component({
  selector: 'ngx-footer',
  styleUrls: ['./footer.component.scss'],
  template: `
    <span class="created-by" style="color: #05fcfc; font-family: Exo; font-size: 1.125rem; font-weight: 400;">I Know You - 2019</span>
    <div class="socials">
      <a href="https://www.twitter.com/kennbroorg" target="_blank" class="ion ion-social-twitter"></a>
    </div>
  `,
})
export class FooterComponent {
}

// <span class="created-by">Created with ♥ by <b><a href="https://akveo.com" target="_blank">Akveo</a></b> 2017</span>
