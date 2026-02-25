"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  UserPlus,
  Shield,
  Eye,
  Settings,
  MoreHorizontal
} from "lucide-react";

const mockUsers = [
  { id: 1, name: "Jean Dupont", role: "Administrateur IT", email: "j.dupont@faceguard.io", lastActive: "Maintenant" },
  { id: 2, name: "Marc Leroy", role: "Chef de Sécurité", email: "m.leroy@faceguard.io", lastActive: "Il y a 2h" },
  { id: 3, name: "Sophie Morel", role: "Agent de Sécurité", email: "s.morel@faceguard.io", lastActive: "Il y a 5 min" },
  { id: 4, name: "Thomas Klein", role: "Agent de Sécurité", email: "t.klein@faceguard.io", lastActive: "Hier" },
];

export default function UsersPage() {
  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-y-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Utilisateurs & Rôles</h1>
          <p className="text-muted-foreground text-sm">Gestion des accès (RBAC) et audit d&apos;activité</p>
        </div>
        <Button className="gap-2">
          <UserPlus className="h-4 w-4" />
          Ajouter un utilisateur
        </Button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roles overview */}
        {[
          { title: "Agent", icon: Eye, desc: "Accès au Live & Triage uniquement", count: 8 },
          { title: "Manager", icon: Shield, desc: "Accès aux Stats & Historique", count: 2 },
          { title: "Admin", icon: Settings, desc: "Contrôle total du système & IA", count: 1 },
        ].map((role, i) => (
          <div key={i} className="p-6 rounded-xl border bg-card space-y-3">
             <div className="flex items-center justify-between">
               <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                 <role.icon className="h-5 w-5" />
               </div>
               <Badge variant="outline">{role.count} utilisateurs</Badge>
             </div>
             <h3 className="font-bold">{role.title}</h3>
             <p className="text-xs text-muted-foreground">{role.desc}</p>
          </div>
        ))}
      </div>

      <div className="border rounded-xl bg-card overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground uppercase text-[10px] font-bold">
            <tr>
              <th className="px-6 py-4">Utilisateur</th>
              <th className="px-6 py-4">Rôle</th>
              <th className="px-6 py-4">Dernière Activité</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {mockUsers.map((user) => (
              <tr key={user.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center font-bold text-xs">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-semibold">{user.name}</span>
                      <span className="text-[10px] text-muted-foreground">{user.email}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <Badge variant="secondary" className="font-medium">{user.role}</Badge>
                </td>
                <td className="px-6 py-4 text-xs text-muted-foreground italic">
                  {user.lastActive}
                </td>
                <td className="px-6 py-4 text-right">
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
