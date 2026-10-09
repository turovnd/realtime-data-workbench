import type { ReactNode } from "react";
import { Activity, Layers3, LogOut, MessageSquareText } from "lucide-react";
import type { Identity } from "@/lib/api/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

type Props = {
  identity: Identity;
  recordCount: number;
  batchCount: number;
  preview: boolean;
  children: ReactNode;
  inspector: ReactNode;
  onLogout: () => void;
  signingOut: boolean;
};
export const WorkspaceShell = ({
  identity,
  recordCount,
  batchCount,
  preview,
  children,
  inspector,
  onLogout,
  signingOut,
}: Props) => (
  <TooltipProvider>
    <SidebarProvider>
      <a
        className="sr-only focus:not-sr-only focus:absolute focus:m-4 focus:bg-background focus:p-3"
        href="#feedback"
      >
        Skip to feedback
      </a>
      <Sidebar>
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild>
                <a href="#feedback">
                  <MessageSquareText />
                  <span className="font-semibold">Feedback Desk</span>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Workspace</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive>
                    <a href="#feedback">
                      <Activity />
                      <span>Feedback stream</span>
                    </a>
                  </SidebarMenuButton>
                  <SidebarMenuBadge>{recordCount}</SidebarMenuBadge>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="#backfills">
                      <Layers3 />
                      <span>Backfill runs</span>
                    </a>
                  </SidebarMenuButton>
                  <SidebarMenuBadge>{batchCount}</SidebarMenuBadge>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <div className="flex flex-col gap-2 px-2 py-3">
            <p className="truncate text-sm">
              {identity.email ?? "Isolated demo workspace"}
            </p>
            <p className="text-xs text-muted-foreground">
              {identity.kind === "account"
                ? "Personal account"
                : "Synthetic data · temporary session"}
            </p>
          </div>
          <Button variant="outline" onClick={onLogout} disabled={signingOut}>
            <LogOut data-icon="inline-start" /> Sign out
          </Button>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-3 border-b px-4 md:px-6">
          <SidebarTrigger />
          <Separator orientation="vertical" className="mr-1 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>Product feedback</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <Badge variant="outline" className="ml-auto">
            {preview ? "Browser preview" : "Connected workspace"}
          </Badge>
        </header>
        <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 p-4 md:p-6 lg:p-8">
          {children}
        </div>
      </SidebarInset>
      {inspector}
    </SidebarProvider>
  </TooltipProvider>
);
