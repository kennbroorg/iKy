import { useMemo } from "react";
import {
  Building2,
  ExternalLink,
  Globe,
  Image,
  Mail,
  MapPin,
  User,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { LocationMap } from "@/components/viz/location-map";
import { getModuleIcon } from "@/lib/icon-map";
import { getModule } from "@/lib/module-registry";
import {
  aggregateProfile,
  type AggregatedProfile,
} from "@/lib/profile-aggregator";
import { useGatherStore } from "@/stores/gather-store";

function EmptyState({ message }: { message: string }) {
  return (
    <p className="py-8 text-center text-sm italic text-muted-foreground">
      {message}
    </p>
  );
}

function ProfileHeader({ profile }: { profile: AggregatedProfile }) {
  const primaryName = profile.names[0] ?? "Unknown";
  const aliases = profile.names.slice(1);
  const photoSrc = profile.photos[0]?.src;

  return (
    <div className="flex items-start gap-6">
      {/* Avatar */}
      <div className="flex size-24 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-primary bg-muted">
        {photoSrc ? (
          <img
            src={photoSrc}
            alt={primaryName}
            className="size-full object-cover"
          />
        ) : (
          <User className="size-12 text-muted-foreground" />
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 space-y-2">
        <h1 className="text-2xl font-bold text-foreground">{primaryName}</h1>
        {aliases.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {aliases.map((alias) => (
              <Badge key={alias} variant="secondary">
                {alias}
              </Badge>
            ))}
          </div>
        )}
        {profile.emails.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Mail className="size-4 shrink-0 text-primary" />
            {profile.emails.map((email) => (
              <span key={email}>{email}</span>
            ))}
          </div>
        )}
        {profile.locations.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <MapPin className="size-4 shrink-0 text-primary" />
            {profile.locations.map((loc) => (
              <span key={loc}>{loc}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function OverviewTab({ profile }: { profile: AggregatedProfile }) {
  const hasOrgs = profile.organizations.length > 0;
  const hasPresence = profile.presence.length > 0;

  if (!hasOrgs && !hasPresence) {
    return <EmptyState message="No overview data available yet." />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {hasOrgs && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="size-4 text-primary" />
              Organizations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {profile.organizations.map((org) => (
                <li
                  key={org}
                  className="text-sm text-muted-foreground"
                >
                  {org}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {hasPresence && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Globe className="size-4 text-primary" />
              Online Presence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {profile.presence.map((p, i) => (
                <li key={`${p.source}-${p.url}-${i}`} className="text-sm">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-primary hover:underline"
                  >
                    <ExternalLink className="size-3 shrink-0" />
                    <span>{p.name ?? p.source}</span>
                  </a>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PhotosTab({ profile }: { profile: AggregatedProfile }) {
  if (profile.photos.length === 0) {
    return <EmptyState message="No photos found." />;
  }

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
      {profile.photos.map((photo, i) => (
        <div
          key={`${photo.src}-${i}`}
          className="group relative overflow-hidden rounded-lg border border-border bg-muted"
        >
          <img
            src={photo.src}
            alt={photo.caption ?? `Photo from ${photo.source}`}
            className="aspect-square w-full object-cover"
          />
          <div className="absolute inset-x-0 bottom-0 bg-black/70 px-2 py-1 text-xs text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
            {photo.source}
            {photo.caption && ` - ${photo.caption}`}
          </div>
        </div>
      ))}
    </div>
  );
}

function SocialTab({ profile }: { profile: AggregatedProfile }) {
  if (profile.social.length === 0) {
    return <EmptyState message="No social data found." />;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {profile.social.map((s, i) => {
        const mod = getModule(s.source);
        const Icon = getModuleIcon(mod?.icon ?? "globe");

        return (
          <Card key={`${s.source}-${s.url}-${i}`}>
            <CardContent className="flex items-center gap-3 pt-6">
              <Icon className="size-5 shrink-0 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">
                  {s.name ?? mod?.label ?? s.source}
                </p>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  <ExternalLink className="size-3" />
                  Visit profile
                </a>
              </div>
              <Badge variant="outline" className="text-[10px]">
                {s.source}
              </Badge>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function MapTab({ profile }: { profile: AggregatedProfile }) {
  if (profile.geo.length === 0) {
    return <EmptyState message="No location data available." />;
  }

  return <LocationMap locations={profile.geo} height="500px" />;
}

export default function ProfilePage() {
  const tasks = useGatherStore((s) => s.tasks);
  const profile = useMemo(() => aggregateProfile(tasks), [tasks]);

  const hasData =
    profile.names.length > 0 ||
    profile.emails.length > 0 ||
    profile.photos.length > 0 ||
    profile.presence.length > 0;

  if (!hasData) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-primary">Profile</h1>
        <EmptyState message="Run a search from the Gatherer page to see profile data." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ProfileHeader profile={profile} />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">
            <User className="size-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="photos">
            <Image className="size-4" />
            Photos
          </TabsTrigger>
          <TabsTrigger value="social">
            <Globe className="size-4" />
            Social
          </TabsTrigger>
          <TabsTrigger value="map">
            <MapPin className="size-4" />
            Map
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab profile={profile} />
        </TabsContent>
        <TabsContent value="photos">
          <PhotosTab profile={profile} />
        </TabsContent>
        <TabsContent value="social">
          <SocialTab profile={profile} />
        </TabsContent>
        <TabsContent value="map">
          <MapTab profile={profile} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
