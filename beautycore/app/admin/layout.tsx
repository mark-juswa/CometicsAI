'use client';

import {InventoryAlerts} from '@/components/inventory-alerts';
import ProtectedRoute from '@/components/ProtectedRoute';
import AdminSidebar from '@/components/AdminSidebar';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute role="admin">
      <div className="min-h-screen">
        <AdminSidebar />
        <div className="lg:pl-60">
          <main className="management-shell min-w-0 px-4 py-6 sm:px-6 lg:px-10 lg:py-8"><InventoryAlerts/>{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
