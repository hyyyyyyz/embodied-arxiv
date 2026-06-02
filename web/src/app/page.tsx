// Daily reading-room homepage. Replaces the previous redirect("/papers")
// — the swipe UI is now reachable via an explicit CTA so first-time visitors
// get masthead / lead / sidebar context before landing in the deck.
//
// Page is a thin server-component shell; the HomeView client component
// owns fetching index.json + the latest day's papers.

import HomeView from "@/components/home/HomeView";

export default function Home() {
  return <HomeView />;
}
