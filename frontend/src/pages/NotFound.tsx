import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section className="prose">
      <h1>Page not found</h1>
      <p>
        <Link to="/" className="text-link">Go back home</Link>
      </p>
    </section>
  );
}
