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
    {
      module: "github",
      param: "johndoe",
      validation: "hard",
      raw: {
        login: "johndoe",
        name: "John Doe",
        bio: "Full-stack developer",
        public_repos: 42,
        followers: 120,
        following: 35,
        created_at: "2015-03-14T12:00:00Z",
      },
      graphic: [
        {
          social: [
            { name: "repos", value: 42 },
            { name: "followers", value: 120 },
            { name: "following", value: 35 },
            { name: "gists", value: 12 },
          ],
        },
      ],
      profile: [
        {
          name: "John Doe",
          email: "johndoe@example.com",
          organization: "Acme Corp",
          location: "San Francisco, CA",
          geo: { lat: 37.7749, lng: -122.4194 },
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
      timeline: [
        { date: "2015-03-14", action: "Account created", icon: "github" },
        { date: "2024-01-15", action: "Last push event", icon: "git-commit" },
      ],
      tasks: [],
    },
  ],
};

export const MOCK_EMAILREP_RESULT = {
  result: [
    {
      module: "emailrep",
      param: "johndoe@example.com",
      validation: "hard",
      raw: {
        email: "johndoe@example.com",
        reputation: "high",
        suspicious: false,
        references: 12,
        details: {
          blacklisted: false,
          malicious_activity: false,
          credentials_leaked: true,
          data_breach: true,
          domain_exists: true,
          domain_reputation: "high",
          profiles: ["github", "twitter", "linkedin"],
        },
      },
      graphic: [
        {
          details: [
            { label: "Reputation", value: "high" },
            { label: "References", value: 12 },
            { label: "Suspicious", value: false },
            { label: "Blacklisted", value: false },
          ],
        },
      ],
      profile: [
        {
          email: "johndoe@example.com",
          presence: [
            {
              source: "GitHub",
              url: "https://github.com/johndoe",
              name: "johndoe",
            },
            {
              source: "Twitter",
              url: "https://twitter.com/johndoe",
              name: "@johndoe",
            },
          ],
        },
      ],
      timeline: [],
      tasks: [],
    },
  ],
};

/** Returns a mock task state that transitions from PENDING → SUCCESS */
export function makeMockTaskState(taskId: string, module: string) {
  return {
    state: "SUCCESS" as const,
    task_id: taskId,
    task_app: module,
  };
}
