'use client';

import {
  LayoutDashboard,
  CalendarDays,
  Users, Package,
  Scissors,
  UserCircle,
} from 'lucide-react';
import Sidebar, { type SidebarLink } from './Sidebar';

const links: SidebarLink[] = [
  { href: '/stylist/inventory', label: 'Salon Supplies', icon: Package },
  { href: '/stylist/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/stylist/appointments', label: 'Appointments', icon: CalendarDays },
  { href: '/stylist/clients', label: 'Clients', icon: Users },
  { href: '/stylist/services', label: 'Services', icon: Scissors },
  { href: '/stylist/profile', label: 'Profile', icon: UserCircle },
];

export default function StylistSidebar() {
  return <Sidebar links={links} portalLabel="Stylist Portal" />;
}
