import type { ApiKey } from "@/types/api";

export const MOCK_MODULES = [
  "emailrep",
  "leaklookup",
  "leaks",
  "holehe",
  "github",
  "twitter",
  "instagram",
  "reddit",
  "sherlock",
  "search",
  "dorks",
  "tiktok",
  "linkedin",
  "spotify",
  "twitch",
  "mastodon",
  "keybase",
  "venmo",
];

export const MOCK_API_KEYS: ApiKey[] = [
  { id: "emailrep_key", name: "EmailRep", key: "mock-emailrep-key-123" },
  {
    id: "haveibeenpwned_key",
    name: "HaveIBeenPwned",
    key: "mock-hibp-key-456",
  },
  {
    id: "peopledatalabs_key",
    name: "PeopleDataLabs",
    key: "mock-pdl-key-789",
  },
];

export const MOCK_GITHUB_RESULT = {
  result: [
    { module: "github" },
    { param: "johndoe" },
    { validation: "hard" },
    {
      raw: {
        login: "johndoe",
        name: "John Doe",
        bio: "Developer",
        public_repos: 42,
        followers: 120,
        following: 35,
      },
    },
    {
      graphic: [
        // graphic[0].github -- gather format for force graph
        {
          github: [
            {
              "name-node": "Github",
              title: "Github",
              subtitle: "",
              icon: "fab fa-github",
              link: "Github",
            },
            {
              "name-node": "GitRepos",
              title: "Repos",
              subtitle: "42",
              icon: "fas fa-folder-open",
              link: "Github",
            },
            {
              "name-node": "GitFollowers",
              title: "Followers",
              subtitle: "120",
              icon: "fas fa-users",
              link: "Github",
            },
            {
              "name-node": "GitFollowing",
              title: "Following",
              subtitle: "35",
              icon: "fas fa-users",
              link: "Github",
            },
            {
              "name-node": "GitGists",
              title: "Gists",
              subtitle: "12",
              icon: "fas fa-code",
              link: "Github",
            },
            {
              "name-node": "GitName",
              title: "Name",
              subtitle: "John Doe",
              icon: "fas fa-user",
              link: "Github",
            },
            {
              "name-node": "GitEmail",
              title: "Email",
              subtitle: "john@example.com",
              icon: "fas fa-envelope",
              link: "Github",
            },
          ],
        },
        // graphic[1].cal_actual -- contribution calendar HTML
        {
          cal_actual:
            '<td data-date="2025-12-01" data-level="2"></td>' +
            '<td data-date="2025-12-02" data-level="3"></td>' +
            '<td data-date="2025-12-03" data-level="1"></td>' +
            '<td data-date="2025-12-04" data-level="0"></td>' +
            '<td data-date="2025-12-05" data-level="4"></td>' +
            '<td data-date="2025-12-06" data-level="2"></td>' +
            '<td data-date="2025-12-07" data-level="1"></td>' +
            '<td data-date="2025-12-08" data-level="3"></td>' +
            '<td data-date="2025-12-09" data-level="2"></td>' +
            '<td data-date="2025-12-10" data-level="0"></td>' +
            '<td data-date="2025-12-11" data-level="1"></td>' +
            '<td data-date="2025-12-12" data-level="4"></td>' +
            '<td data-date="2025-12-13" data-level="2"></td>' +
            '<td data-date="2025-12-14" data-level="3"></td>',
        },
      ],
    },
    {
      profile: [
        {
          name: "John Doe",
          email: "john@example.com",
          organization: "Acme Corp",
          location: "San Francisco",
          geo: { lat: 37.77, lng: -122.42 },
          photos: [
            {
              src: "https://avatars.githubusercontent.com/u/123456",
              caption: "GitHub avatar",
            },
          ],
          presence: [
            {
              source: "GitHub",
              url: "https://github.com/johndoe",
              name: "johndoe",
            },
          ],
        },
      ],
    },
    {
      timeline: [
        { date: "2015-03-14", action: "Account created", icon: "github" },
      ],
    },
    { tasks: [] },
  ],
};

export const MOCK_TWITTER_RESULT = {
  result: [
    { module: "twitter" },
    { param: "johndoe" },
    { validation: "soft" },
    { raw: {} },
    {
      graphic: [
        // [0] social -- gather format
        {
          social: [
            {
              "name-node": "Twitter",
              title: "Twitter",
              subtitle: "",
              icon: "fab fa-twitter",
              link: "Twitter",
            },
            {
              "name-node": "TwFollowers",
              title: "Followers",
              subtitle: "1250",
              icon: "fas fa-users",
              link: "Twitter",
            },
            {
              "name-node": "TwFollowing",
              title: "Following",
              subtitle: "340",
              icon: "fas fa-users",
              link: "Twitter",
            },
            {
              "name-node": "TwTweets",
              title: "Tweets",
              subtitle: "5420",
              icon: "fas fa-comment",
              link: "Twitter",
            },
            {
              "name-node": "TwLikes",
              title: "Likes",
              subtitle: "12300",
              icon: "fas fa-heart",
              link: "Twitter",
            },
          ],
        },
        // [1] resume
        {
          resume: {
            children: [
              { name: "Following", total: 340 },
              { name: "Followers", total: 1250 },
              { name: "Tweets", total: 5420 },
              { name: "Likes", total: 12300 },
            ],
          },
        },
        // [2] popularity
        {
          popularity: [
            { title: "Following", value: 340 },
            { title: "Followers", value: 1250 },
          ],
        },
        // [3] approval
        {
          approval: [
            { title: "Tweets", value: 5420 },
            { title: "Likes", value: 12300 },
          ],
        },
        // [4] hashtag
        {
          hashtag: [
            { label: "#javascript", value: 15 },
            { label: "#react", value: 12 },
            { label: "#typescript", value: 10 },
            { label: "#nodejs", value: 8 },
            { label: "#webdev", value: 7 },
            { label: "#opensource", value: 5 },
          ],
        },
        // [5] users -- gather format
        {
          users: [
            {
              "name-node": "Users",
              title: "Users",
              subtitle: "",
              icon: "fas fa-users",
              link: "Users",
            },
            {
              "name-node": "U1",
              title: "@reactjs",
              subtitle: "5",
              icon: "fas fa-at",
              link: "Users",
            },
            {
              "name-node": "U2",
              title: "@vercel",
              subtitle: "3",
              icon: "fas fa-at",
              link: "Users",
            },
            {
              "name-node": "U3",
              title: "@nodejs",
              subtitle: "2",
              icon: "fas fa-at",
              link: "Users",
            },
          ],
        },
        // [6] tweetslist
        {
          tweetslist: [
            { name: "Tweet 1", retweets: 5, likes: 20, replies: 3 },
            { name: "Tweet 2", retweets: 12, likes: 45, replies: 8 },
            { name: "Tweet 3", retweets: 2, likes: 10, replies: 1 },
            { name: "Tweet 4", retweets: 25, likes: 80, replies: 15 },
          ],
        },
        // [7] week
        {
          week: [
            { name: "Mon", value: 12 },
            { name: "Tue", value: 15 },
            { name: "Wed", value: 8 },
            { name: "Thu", value: 20 },
            { name: "Fri", value: 18 },
            { name: "Sat", value: 5 },
            { name: "Sun", value: 3 },
          ],
        },
        // [8] hour
        {
          hour: [
            { name: "0", value: 1 },
            { name: "6", value: 3 },
            { name: "9", value: 8 },
            { name: "12", value: 15 },
            { name: "15", value: 12 },
            { name: "18", value: 10 },
            { name: "21", value: 6 },
          ],
        },
        // [9] sources
        {
          sources: [
            { name: "Twitter Web App", value: 45 },
            { name: "iPhone", value: 30 },
            { name: "TweetDeck", value: 15 },
            { name: "Android", value: 10 },
          ],
        },
        // [10] time
        {
          time: [
            { name: "2025-01", value: 45 },
            { name: "2025-02", value: 52 },
            { name: "2025-03", value: 38 },
            { name: "2025-04", value: 60 },
            { name: "2025-05", value: 42 },
            { name: "2025-06", value: 55 },
          ],
        },
        // [11] twvsrt
        {
          twvsrt: [
            { title: "Tweets", value: 3800 },
            { title: "Retweets", value: 1620 },
          ],
        },
      ],
    },
    {
      profile: [
        {
          name: "John Doe",
          presence: [
            {
              source: "Twitter",
              url: "https://twitter.com/johndoe",
              name: "@johndoe",
            },
          ],
        },
      ],
    },
    { timeline: [] },
    { tasks: [] },
  ],
};

export const MOCK_HOLEHE_RESULT = {
  result: [
    { module: "holehe" },
    { param: "johndoe@example.com" },
    { validation: "hard" },
    { raw: {} },
    {
      graphic: [
        {
          holehe: [
            {
              "name-node": "Holehe",
              title: "Holehe",
              subtitle: "johndoe@example.com",
              icon: "fas fa-at",
              link: "Holehe",
            },
            {
              "name-node": "HTwitter",
              title: "twitter.com",
              icon: "fab fa-twitter",
              link: "Holehe",
            },
            {
              "name-node": "HGithub",
              title: "github.com",
              icon: "fab fa-github",
              link: "Holehe",
            },
            {
              "name-node": "HSpotify",
              title: "spotify.com",
              icon: "fab fa-spotify",
              link: "Holehe",
            },
          ],
        },
        {
          lists: [
            {
              title: "twitter.com",
              exists: true,
              rateLimit: false,
              emailrecovery: "j***@example.com",
              phoneNumber: null,
            },
            {
              title: "github.com",
              exists: true,
              rateLimit: false,
              emailrecovery: null,
              phoneNumber: null,
            },
            {
              title: "spotify.com",
              exists: true,
              rateLimit: false,
              emailrecovery: null,
              phoneNumber: null,
            },
            {
              title: "instagram.com",
              exists: false,
              rateLimit: false,
              emailrecovery: null,
              phoneNumber: null,
            },
            {
              title: "facebook.com",
              exists: false,
              rateLimit: true,
              emailrecovery: null,
              phoneNumber: null,
            },
          ],
        },
      ],
    },
    {
      profile: [
        {
          social: [
            {
              source: "Twitter",
              url: "https://twitter.com",
              name: "twitter.com",
            },
          ],
        },
      ],
    },
    { timeline: [] },
    { tasks: [] },
  ],
};

export const MOCK_SEARCH_RESULT = {
  result: [
    { module: "search" },
    { param: "johndoe" },
    { validation: "no" },
    { raw: {} },
    {
      graphic: [
        {
          names: [
            { label: "John Doe", value: 5 },
            { label: "J. Doe", value: 2 },
          ],
        },
        {
          username: [
            { label: "johndoe", value: 8 },
            { label: "john_doe", value: 3 },
          ],
        },
        {
          social: [
            {
              "name-node": "Social",
              title: "Social",
              subtitle: "",
              icon: "fas fa-share-alt",
              link: "Social",
            },
            {
              "name-node": "SGithub",
              title: "GitHub",
              subtitle: "johndoe",
              icon: "fab fa-github",
              link: "Social",
            },
            {
              "name-node": "SLinkedin",
              title: "LinkedIn",
              subtitle: "johndoe",
              icon: "fab fa-linkedin",
              link: "Social",
            },
          ],
        },
        {
          rawresults: [
            {
              title: "John Doe [google]",
              simple: "John Doe - GitHub",
              url: "https://github.com/johndoe",
              desc: "Developer profile",
              icon: "fas fa-searchengin",
              link: "google",
            },
            {
              title: "John Doe [google]",
              simple: "John Doe | LinkedIn",
              url: "https://linkedin.com/in/johndoe",
              desc: "Professional profile",
              icon: "fas fa-searchengin",
              link: "google",
            },
          ],
        },
        {
          searches: [
            {
              title: "John Doe [google]",
              simple: "John Doe - GitHub",
              url: "https://github.com/johndoe",
              desc: "Developer profile",
              icon: "fas fa-searchengin",
              link: "google",
            },
          ],
        },
        {
          mentions: [{ label: "@johndoe", value: 3 }],
        },
        {
          hashtags: [
            { label: "#developer", value: 4 },
            { label: "#tech", value: 2 },
          ],
        },
        {
          emails: [{ label: "johndoe@example.com", value: 2 }],
        },
      ],
    },
    { profile: [{ name: "John Doe" }] },
    { timeline: [] },
    { tasks: [] },
  ],
};

export const MOCK_EMAILREP_RESULT = {
  result: [
    { module: "emailrep" },
    { param: "johndoe@example.com" },
    { validation: "hard" },
    {
      raw: {
        email: "johndoe@example.com",
        reputation: "high",
        suspicious: false,
      },
    },
    {
      graphic: [
        {
          details: [
            {
              "name-node": "EmailRep",
              title: "EmailRep",
              subtitle: "johndoe@example.com",
              icon: "fas fa-envelope",
              link: "EmailRep",
            },
            {
              "name-node": "ERRep",
              title: "Reputation",
              subtitle: "high",
              icon: "fas fa-star",
              link: "EmailRep",
            },
            {
              "name-node": "ERSusp",
              title: "Suspicious",
              subtitle: "false",
              icon: "fas fa-shield-alt",
              link: "EmailRep",
            },
            {
              "name-node": "ERRefs",
              title: "References",
              subtitle: "12",
              icon: "fas fa-link",
              link: "EmailRep",
            },
          ],
        },
        {
          social: [
            {
              "name-node": "Social",
              title: "Social",
              subtitle: "",
              icon: "fas fa-share-alt",
              link: "Social",
            },
            {
              "name-node": "SGithub",
              title: "GitHub",
              subtitle: "johndoe",
              icon: "fab fa-github",
              link: "Social",
            },
            {
              "name-node": "STwitter",
              title: "Twitter",
              subtitle: "@johndoe",
              icon: "fab fa-twitter",
              link: "Social",
            },
          ],
        },
      ],
    },
    {
      profile: [
        {
          email: "johndoe@example.com",
          presence: [
            {
              source: "GitHub",
              url: "https://github.com/johndoe",
              name: "johndoe",
            },
          ],
        },
      ],
    },
    { timeline: [] },
    { tasks: [] },
  ],
};

/** Returns a mock task state that transitions from PENDING -> SUCCESS */
export function makeMockTaskState(taskId: string, module: string) {
  return {
    state: "SUCCESS" as const,
    task_id: taskId,
    task_app: module,
  };
}
