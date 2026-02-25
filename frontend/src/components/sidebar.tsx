"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  AlertTriangle,
  History,
  BarChart3,
  Cctv,
  Users,
  ShieldCheck
} from "lucide-react";

const navigation = [
  {
    title: "Pôle Opérationnel",
    items: [
      { name: "Surveillance Live", href: "/", icon: LayoutDashboard },
      { name: "Gestion des Alertes", href: "/alerts", icon: AlertTriangle },
    ],
  },
  {
    title: "Pôle Managérial",
    items: [
      { name: "Historique & Logs", href: "/history", icon: History },
      { name: "Statistiques", href: "/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "Pôle Technique",
    items: [
      { name: "Caméras", href: "/devices", icon: Cctv },
      { name: "Configuration IA", href: "/settings/ia", icon: ShieldCheck },
      { name: "Utilisateurs", href: "/settings/users", icon: Users },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card text-card-foreground">
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          <ShieldCheck className="h-6 w-6 text-primary" />
          <span>FaceGuard <span className="text-xs text-muted-foreground font-normal">v2.0</span></span>
        </Link>
      </div>
      <nav className="flex-1 overflow-y-auto p-4 space-y-8">
        {navigation.map((section) => (
          <div key={section.title}>
            <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {section.title}
            </h3>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t p-4">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
            <Users className="h-4 w-4 text-primary" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">Admin User</span>
            <span className="text-xs text-muted-foreground">Administrateur</span>
          </div>
        </div>
      </div>
    </div>
  );
}
