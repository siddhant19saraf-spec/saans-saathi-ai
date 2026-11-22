import { describe, expect, it } from "vitest";

import {
  allNavItems,
  findActiveNavItem,
  navGroups,
  navTrail,
  settingsItem,
} from "@/components/navigation/nav-config";

describe("nav-config", () => {
  it("finds an exact route and a nested route, but not an unknown path", () => {
    expect(findActiveNavItem("/dashboard")?.label).toBe("Dashboard");
    expect(findActiveNavItem("/dashboard/details")?.label).toBe("Dashboard");
    expect(findActiveNavItem("/nope")).toBeNull();
  });

  it("builds a breadcrumb trail for groups and settings only", () => {
    expect(navTrail("/smart-routine")?.group).toBe("Protection");
    expect(navTrail("/smart-routine/2026-11-21")?.item.label).toBe("SmartRoutine");
    expect(navTrail("/settings")).toEqual({ group: "Workspace", item: settingsItem });
    expect(navTrail("/settings/profile")).toBeNull();
    expect(navTrail("/nope")).toBeNull();
  });

  it("exposes every grouped destination plus settings", () => {
    const grouped = navGroups.flatMap((group) => group.items);
    expect(allNavItems).toEqual([...grouped, settingsItem]);
  });
});
