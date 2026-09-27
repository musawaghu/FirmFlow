import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/** New page, new scroll position. Links to a passage (#passage-…) scroll themselves. */
export function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}
