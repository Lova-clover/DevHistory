/**
 * Lightweight analytics helper.
 * Fires events to POST /api/analytics/event.  Never throws.
 */

export interface AnalyticsEvent {
  event_name: string;
  path?: string;
  referrer?: string;
  meta?: Record<string, unknown>;
}

export function trackEvent(event: AnalyticsEvent): void {
  if (typeof window === "undefined") return;

  fetch("/api/analytics/event", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_name: event.event_name,
      path: event.path ?? window.location.pathname,
      referrer: event.referrer ?? document.referrer || null,
      meta: event.meta ?? null,
    }),
  }).catch(() => {
    // analytics must never break the app
  });
}
