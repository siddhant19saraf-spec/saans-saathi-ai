import { Breadcrumbs } from "@/components/navigation/breadcrumbs";
import { CommandSearch } from "@/components/navigation/command-search";
import { LocationSwitcher } from "@/components/navigation/location-switcher";
import { Notifications } from "@/components/navigation/notifications";
import { UserMenu } from "@/components/navigation/user-menu";

import { MobileNav } from "./mobile-nav";

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/85 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-2 px-4 sm:px-6 lg:px-8">
        <MobileNav />
        <div className="mr-auto hidden min-w-0 md:block">
          <Breadcrumbs />
        </div>
        <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
          <CommandSearch />
          <LocationSwitcher />
          <Notifications />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
