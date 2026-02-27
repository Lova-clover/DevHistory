"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { trackEvent } from "@/lib/analytics";

/**
 * Fires a `page_view` event to /api/analytics/event on every
 * client-side route change.  Mounted once in the root layout.
 */
export function AnalyticsTracker() {
  const pathname = usePathname();
  const prev = useRef<string | null>(null);
  const startRef = useRef<number>(Date.now());

  useEffect(() => {
    // On path change, send duration of previous page
    const now = Date.now();
    const durationMs = now - startRef.current;
    startRef.current = now;

    // Skip duplicate fires for the same path (e.g. re-renders)
    if (pathname === prev.current) return;

    // Send page_view with duration of *previous* page
    trackEvent({
      event_name: "page_view",
      path: pathname,
      meta: {
        source: "spa_navigation",
        prev_path: prev.current,
        prev_duration_ms: prev.current ? durationMs : null,
      },
    });

    prev.current = pathname;
  }, [pathname]);

  return null;
}
