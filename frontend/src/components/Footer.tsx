import { Link } from "react-router-dom";
import { openChat } from "../chatEvents";
import BrandMark from "./BrandMark";

const SHOP = ["Hoodies", "Crewnecks", "T-Shirts", "Quarter-Zips", "Jackets & Fleece"];

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div>
          <BrandMark />
          <p>Yale apparel for students, families and alumni — residential college gear, varsity sports and The Game.</p>
        </div>
        <nav aria-label="Shop">
          <h2>Shop</h2>
          <ul>
            {SHOP.map((c) => (
              <li key={c}>
                <Link to={`/products?category=${encodeURIComponent(c)}`}>{c}</Link>
              </li>
            ))}
          </ul>
        </nav>
        <nav aria-label="Help">
          <h2>Help</h2>
          <ul>
            <li>
              <button type="button" className="text-link footer-chat" onClick={() => openChat()}>
                Ask the shopping assistant
              </button>
            </li>
            <li>
              <Link to="/about">About Us</Link>
            </li>
            <li>
              <Link to="/login">Log in</Link>
            </li>
            <li>
              <Link to="/create-account">Create account</Link>
            </li>
          </ul>
        </nav>
      </div>
      <p className="footer-bottom">© 2026 Campus Customs · New Haven, CT</p>
    </footer>
  );
}
