import { NbMenuItem } from '@nebular/theme';

export const MENU_ITEMS: NbMenuItem[] = [
  {
    title: 'Principal',
    icon: 'home',
    link: '/pages/principal',
    home: true,
  },
  {
    title: 'Gatherer',
    icon: 'binoculars',
    link: '/pages/gatherer',
  },
  {
    title: 'Profile',
    icon: 'user',
    link: '/pages/profile',
  },
  {
    title: 'Timeline',
    icon: 'stopwatch',
    link: '/pages/timeline',
  },
  {
    title: 'ApiKeys',
    icon: 'key',  
    link: '/pages/apikeys',
  },
  // {
  //   title: 'Comparison',
  //   icon: 'chart-bar',
  //   children: [
  //     {
  //       title: 'Twitter',
  //       icon: { icon: 'twitter', pack: 'fab' },
  //       link: '/pages/comparison',
  //     },
  //   ],
  // },
];
