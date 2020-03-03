import { Component } from '@angular/core';

@Component({
  selector: 'ngx-footer',
  styleUrls: ['./footer.component.scss'],
  template: `
    <span class="created-by" style="color: #05fcfc; font-family: Exo; font-size: 1.125rem; font-weight: 400;">I Know You - 2020</span>
    <div class="socials">
      <a href="https://www.twitter.com/kennbroorg" target="_blank" class="ion ion-social-twitter"></a>
    </div>
    <div class="socials">
      <a href="https://www.instagram.com/kennbroorg" target="_blank" class="ion ion-social-instagram"></a>
    </div>
    <div class="socials">
      <a href="https://www.vimeo.com/user85580359" target="_blank" class="ion ion-social-vimeo"></a>
    </div>
    <div class="socials">
      <a href="https://https://github.com/kennbroorg/iKy" target="_blank" class="ion ion-social-github"></a>
    </div>
    <div class="socials">
      <a target="_blank" href="https://gitlab.com/kennbroorg/iKy"><i class="fab fa-gitlab"></i></a>
    </div>
  `,
})
export class FooterComponent {
}
