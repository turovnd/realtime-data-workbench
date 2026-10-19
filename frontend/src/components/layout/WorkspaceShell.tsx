import type { ReactNode } from "react";
import { useEffect } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Activity, Inbox, LogOut, MessageSquareText } from "lucide-react";

import type { Identity } from "@/api";
import {
  Avatar,
  AvatarFallback,
  Badge,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
  Button,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  TooltipProvider,
  useSidebar,
} from "@/components/ui";

type Props = {
  identity: Identity;
  children: ReactNode;
  onLogout: () => void;
  signingOut: boolean;
};

const RouteEffects = () => {
  const { pathname } = useLocation();
  const { setOpenMobile } = useSidebar();

  useEffect(() => {
    setOpenMobile(false);
  }, [pathname, setOpenMobile]);

  return null;
};

const Navigation = () => {
  const location = useLocation();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          asChild
          isActive={location.pathname.startsWith("/feedback")}
        >
          <NavLink to="/feedback">
            <Inbox />
            <span>Inbox</span>
          </NavLink>
        </SidebarMenuButton>
      </SidebarMenuItem>
      <SidebarMenuItem>
        <SidebarMenuButton asChild isActive={location.pathname === "/activity"}>
          <NavLink to="/activity">
            <Activity />
            <span>Activity</span>
          </NavLink>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};

export const WorkspaceShell = ({
  identity,
  children,
  onLogout,
  signingOut,
}: Props) => {
  const location = useLocation();
  const detail = location.pathname.startsWith("/feedback/");
  const title = location.pathname === "/activity" ? "Activity" : "Inbox";
  const demo = identity.kind !== "account";

  useEffect(() => {
    document.title = `${detail ? "Feedback details" : title} · Feedback Desk`;
  }, [detail, title]);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [location.pathname]);

  return (
    <TooltipProvider>
      <SidebarProvider>
        <RouteEffects />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:m-4 focus:bg-background focus:p-3"
        >
          Skip to content
        </a>
        <Sidebar variant="inset">
          <SidebarHeader className="px-4 py-5">
            <Link to="/feedback" className="flex items-center gap-3">
              <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <MessageSquareText className="size-5" />
              </span>
              <span className="font-semibold tracking-tight">
                Feedback Desk
              </span>
            </Link>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <Navigation />
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="gap-3 p-4">
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback>
                  {demo ? "D" : identity.email?.slice(0, 1).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {demo ? "Demo workspace" : identity.email}
                </p>
                <p className="text-xs text-muted-foreground">
                  {demo ? "Your own sample data" : "Personal workspace"}
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={onLogout} disabled={signingOut}>
              <LogOut data-icon="inline-start" />
              {signingOut ? "Signing out…" : "Sign out"}
            </Button>
          </SidebarFooter>
        </Sidebar>
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-3 border-b px-4 md:px-6">
            <SidebarTrigger />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  {detail ? (
                    <BreadcrumbLink asChild>
                      <Link to={`/feedback${location.search}`}>Inbox</Link>
                    </BreadcrumbLink>
                  ) : (
                    <BreadcrumbPage>{title}</BreadcrumbPage>
                  )}
                </BreadcrumbItem>
                {detail && (
                  <>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbPage>Feedback details</BreadcrumbPage>
                    </BreadcrumbItem>
                  </>
                )}
              </BreadcrumbList>
            </Breadcrumb>
            {demo && (
              <Badge variant="secondary" className="ml-auto">
                {identity.kind === "browser-demo" ? "Demo preview" : "Demo"}
              </Badge>
            )}
          </header>
          <main
            id="main-content"
            tabIndex={-1}
            className="mx-auto flex w-full max-w-7xl min-w-0 flex-col gap-6 p-4 outline-none md:p-6 lg:p-8"
          >
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
};
