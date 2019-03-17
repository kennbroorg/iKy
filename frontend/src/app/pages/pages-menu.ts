import { NbMenuItem } from '@nebular/theme';

export const MENU_ITEMS: NbMenuItem[] = [
  {
    title: 'Principal',
    icon: 'fa fa-home',
    link: '/pages/principal',
    home: true,
  },
  {
    title: 'Gatherer',
    icon: 'fa fa-binoculars',
    link: '/pages/gatherer',
  },
  {
    title: 'Profile',
    icon: 'fas fa-user',
    link: '/pages/profile',
  },
  {
    title: 'Timeline',
    icon: 'fas fa-stopwatch',
    link: '/pages/timeline',
  },
  {
    title: 'ApiKeys',
    icon: 'fas fa-key',  
    link: '/pages/apikeys',
  },
];
