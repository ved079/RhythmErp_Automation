"use client";

import {
  LayoutDashboard,
  FlaskConical,
  FileText,
  Settings,
  LogOut,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { usePathname, useRouter } from "next/navigation";

const mainNav = [
  { title: "Dashboard", icon: LayoutDashboard, path: "/" },
  { title: "Test Runs", icon: FlaskConical, path: "/runs" },
  { title: "Reports", icon: FileText, path: "/reports" },
];

const systemNav = [
  { title: "Settings", icon: Settings, path: "/settings" },
];

interface AppSidebarProps {
  onSignOut: () => void;
}

export function AppSidebar({ onSignOut }: AppSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const stored =
    typeof window !== "undefined" ? localStorage.getItem("pacs_user") : null;
  const user = stored ? JSON.parse(stored) : { displayName: "User", username: "user" };
  const initials = user.displayName
    ?.split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";

  return (
    <Sidebar className="border-r border-border">
      {/* Logo */}
      <SidebarHeader className="px-4 py-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="size-7 rounded-md bg-foreground flex items-center justify-center flex-shrink-0">
            <FlaskConical className="size-3.5 text-background" />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-foreground leading-none">PACS</p>
            <p className="text-[10px] text-muted-foreground mt-0.5 leading-none">Automation Portal</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-3 py-3">
        {/* Main nav */}
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="px-2 text-[10px] font-medium text-muted-foreground/70 uppercase tracking-wider mb-1">
            Overview
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={pathname === item.path}
                    onClick={() => router.push(item.path)}
                    className="h-8 text-[13px] rounded-md px-2 gap-2 text-muted-foreground data-[active=true]:text-foreground data-[active=true]:bg-accent data-[active=true]:font-medium hover:text-foreground hover:bg-accent/60 transition-colors"
                  >
                    <item.icon className="size-3.5 flex-shrink-0" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* System nav */}
        <SidebarGroup className="p-0 mt-4">
          <SidebarGroupLabel className="px-2 text-[10px] font-medium text-muted-foreground/70 uppercase tracking-wider mb-1">
            System
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {systemNav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={pathname === item.path}
                    onClick={() => router.push(item.path)}
                    className="h-8 text-[13px] rounded-md px-2 gap-2 text-muted-foreground data-[active=true]:text-foreground data-[active=true]:bg-accent data-[active=true]:font-medium hover:text-foreground hover:bg-accent/60 transition-colors"
                  >
                    <item.icon className="size-3.5 flex-shrink-0" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* User footer */}
      <SidebarFooter className="border-t border-border px-3 py-3">
        <div className="flex items-center gap-2 px-2 py-1">
          <div className="size-6 rounded-full bg-foreground/10 flex items-center justify-center flex-shrink-0">
            <span className="text-[9px] font-semibold text-foreground">{initials}</span>
          </div>
          <div className="flex flex-col min-w-0 flex-1">
            <span className="text-[12px] font-medium text-foreground truncate leading-none">{user.displayName}</span>
            <span className="text-[10px] text-muted-foreground truncate leading-none mt-0.5">{user.username}</span>
          </div>
          <button
            onClick={onSignOut}
            className="size-6 rounded-md flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors flex-shrink-0"
            title="Sign out"
          >
            <LogOut className="size-3" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}