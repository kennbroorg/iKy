import { RouterModule, Routes } from '@angular/router';
import { NgModule } from '@angular/core';

import { PagesComponent } from './pages.component';
import { PrincipalComponent } from './principal/principal.component';
import { GathererComponent } from './gatherer/gatherer.component';
import { ProfileComponent } from './profile/profile.component';
import { TimelineComponent } from './timeline/timeline.component';
import { ApiKeysComponent } from './apikeys/apikeys.component';
// import { ComparisonComponent } from './comparison/comparison.component';

import { NotFoundComponent } from './miscellaneous/not-found/not-found.component';

const routes: Routes = [{
  path: '',
  component: PagesComponent,
  children: [
    {
      path: 'principal',
      component: PrincipalComponent,
    }, {
      path: 'gatherer',
      component: GathererComponent,
    }, {
      path: 'profile',
      component: ProfileComponent,
    }, {
      path: 'timeline',
      component: TimelineComponent,
    }, {
      path: 'apikeys',
      component: ApiKeysComponent,
    }, {
    //   path: 'comparison',
    //   component: ComparisonComponent,
    // }, {
      path: '',
      redirectTo: 'principal',
      pathMatch: 'full',
    }, {
      path: '**',
      component: NotFoundComponent,
    },
  ],
}];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PagesRoutingModule {
}
