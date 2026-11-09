"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import ClientSidebar from "@/components/ClientSidebar";
import { BookingNotifications } from "@/components/booking-notifications";
import { GenerationProvider } from "@/components/generation-provider";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute role="client">
      <div className="min-h-screen">
        <ClientSidebar />
        <BookingNotifications />
        <div className="pt-16 lg:pl-60">
          <main className="px-6 py-8 lg:px-10"><GenerationProvider>{children}</GenerationProvider></main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
