"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

/**
 * Fires a `page_view` event to /api/analytics/event on every
 * client-side route change.  Mounted once in the root layout.
 */
export function AnalyticsTracker() {
  const pathname = usePathname();
  const prev = useRef<string | null>(null);

  useEffect(() => {
    // Skip duplicate fires for the same path (e.g. re-renders)
    if (pathname === prev.current) return;
    prev.current = pathname;

    fetch("/api/analytics/event", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_name: "page_view",
        path: pathname,
        referrer: document.referrer || null,
      }),
    }).catch(() => {
      // analytics should never break the app
    });
  }, [pathname]);

  return null;
}
