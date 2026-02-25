import type { TaskEntry } from "@/stores/gather-store";

export interface AggregatedProfile {
  names: string[];
  emails: string[];
  organizations: string[];
  locations: string[];
  photos: { src: string; caption?: string; source: string }[];
  presence: { source: string; url: string; name?: string }[];
  social: { source: string; url: string; name?: string }[];
  geo: { lat: number; lng: number; label: string }[];
}

export function aggregateProfile(
  tasks: Record<string, TaskEntry>,
): AggregatedProfile {
  const profile: AggregatedProfile = {
    names: [],
    emails: [],
    organizations: [],
    locations: [],
    photos: [],
    presence: [],
    social: [],
    geo: [],
  };

  for (const [moduleName, task] of Object.entries(tasks)) {
    if (task.status !== "success" || !task.result?.profile) continue;
    for (const item of task.result.profile) {
      if (
        item.name &&
        typeof item.name === "string" &&
        !profile.names.includes(item.name)
      )
        profile.names.push(item.name);
      if (
        item.email &&
        typeof item.email === "string" &&
        !profile.emails.includes(item.email)
      )
        profile.emails.push(item.email);
      if (
        item.organization &&
        typeof item.organization === "string" &&
        !profile.organizations.includes(item.organization)
      )
        profile.organizations.push(item.organization);
      if (
        item.location &&
        typeof item.location === "string" &&
        !profile.locations.includes(item.location)
      )
        profile.locations.push(item.location);
      if (item.photos && Array.isArray(item.photos)) {
        for (const p of item.photos as { src: string; caption?: string }[]) {
          profile.photos.push({ ...p, source: moduleName });
        }
      }
      if (item.presence && Array.isArray(item.presence))
        profile.presence.push(
          ...(item.presence as { source: string; url: string }[]),
        );
      if (item.social && Array.isArray(item.social))
        profile.social.push(
          ...(item.social as { source: string; url: string }[]),
        );
      if (
        item.geo &&
        typeof item.geo === "object" &&
        item.geo !== null
      ) {
        const g = item.geo as { lat: number; lng: number };
        if (typeof g.lat === "number" && typeof g.lng === "number")
          profile.geo.push({ ...g, label: moduleName });
      }
    }
  }

  return profile;
}
