import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/** Start each page at the top, e.g. after clicking a card far down a grid. */
export default function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}
