import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import BrandMark from "./BrandMark";

const mainLinks = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products", end: false },
  { to: "/about", label: "About Us", end: false },
];

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "nav-link active" : "nav-link";

export default function NavBar() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <>
      {/* Only true, checkable facts here — no invented shipping or return promises. */}
      <p className="announce">
        <strong>Yale gear from New Haven</strong> · Sizes XS–XXL with live stock · Questions? Ask our shopping
        assistant
      </p>
      <header className="navbar">
        <BrandMark />
        <nav aria-label="Main" className="nav-links">
          {mainLinks.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={navClass}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="nav-account">
          {loading ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button type="button" className="button button-small button-ghost" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navClass}>
                Log in
              </NavLink>
              <NavLink to="/create-account" className="button button-small">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </header>
    </>
  );
}
