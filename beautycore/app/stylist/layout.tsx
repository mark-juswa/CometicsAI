"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import StylistSidebar from "@/components/StylistSidebar";
import { BookingNotifications } from "@/components/booking-notifications";

export default function StylistLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute role="stylist">
      <div className="min-h-screen">
        <StylistSidebar />
        <BookingNotifications />
        <div className="pt-16 lg:pl-60">
          <main className="management-shell min-w-0 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
