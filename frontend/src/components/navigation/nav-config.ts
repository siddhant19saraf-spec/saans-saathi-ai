import {
  CalendarClock,
  House,
  Leaf,
  LayoutDashboard,
  MapPinned,
  Route,
  Settings2,
  Sparkles,
  Users,
  Wind,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  keywords: string[];
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const navGroups: NavGroup[] = [
  {
    label: "Workspace",
    items: [
      {
        href: "/dashboard",
        label: "Dashboard",
        description: "Current conditions, provenance and household actions.",
        icon: LayoutDashboard,
        keywords: ["home", "overview", "aqi", "today"],
      },
      {
        href: "/air-quality",
        label: "Air intelligence",
        description: "Pollutants, CPCB AQI method, forecast and history.",
        icon: Wind,
        keywords: ["pollution", "pm2.5", "pm10", "no2", "forecast"],
      },
      {
        href: "/map",
        label: "Pollution map",
        description: "Choose a location on an OpenStreetMap view.",
        icon: MapPinned,
        keywords: ["location", "station", "openstreetmap"],
      },
    ],
  },
  {
    label: "Personal protection",
    items: [
      {
        href: "/family",
        label: "Family intelligence",
        description: "Household profile, sensitivities and preferences.",
        icon: Users,
        keywords: ["household", "members", "children", "asthma"],
      },
      {
        href: "/smart-routine",
        label: "SmartRoutine",
        description: "Plan the day around lower-exposure windows.",
        icon: CalendarClock,
        keywords: ["schedule", "planner", "activity", "timing"],
      },
      {
        href: "/indoor-shield",
        label: "IndoorShield",
        description: "Ventilation, dust, kitchen and filtration guidance.",
        icon: House,
        keywords: ["indoor", "ventilation", "purifier", "kitchen"],
      },
    ],
  },
  {
    label: "Sustainability",
    items: [
      {
        href: "/eco-route",
        label: "EcoRoute",
        description: "Compare travel modes and see stated assumptions.",
        icon: Route,
        keywords: ["travel", "commute", "carbon", "transport"],
      },
      {
        href: "/impact",
        label: "Impact intelligence",
        description: "Log environmental actions and review assumptions.",
        icon: Leaf,
        keywords: ["carbon", "savings", "history", "sustainability"],
      },
    ],
  },
  {
    label: "Assistance",
    items: [
      {
        href: "/copilot",
        label: "SAANS AI Copilot",
        description: "Ask grounded questions about your air-quality data.",
        icon: Sparkles,
        keywords: ["ai", "assistant", "chat", "gemini"],
      },
    ],
  },
];

export const settingsItem: NavItem = {
  href: "/settings",
  label: "Settings",
  description: "Notifications, data sources, privacy, local data and accessibility.",
  icon: Settings2,
  keywords: ["preferences", "privacy", "data", "account", "accessibility"],
};

export const allNavItems: NavItem[] = [...navGroups.flatMap((group) => group.items), settingsItem];

export function findActiveNavItem(pathname: string): NavItem | null {
  return (
    allNavItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ??
    null
  );
}

export function navTrail(pathname: string): { group: string; item: NavItem } | null {
  for (const group of navGroups) {
    const item = group.items.find(
      (candidate) => pathname === candidate.href || pathname.startsWith(`${candidate.href}/`),
    );
    if (item) {
      return { group: group.label, item };
    }
  }
  if (pathname === settingsItem.href) {
    return { group: "Preferences", item: settingsItem };
  }
  return null;
}
