import { Link } from "react-router-dom";

/** Shield monogram + wordmark used in the nav bar and footer. */
export default function BrandMark() {
  return (
    <Link to="/" className="brand" aria-label="Campus Customs home">
      <svg className="brand-mark" viewBox="0 0 34 38" aria-hidden="true">
        <path
          d="M17 1.5 31.5 6v12.2c0 8.6-6 15.4-14.5 18.3C8.5 33.6 2.5 26.8 2.5 18.2V6L17 1.5Z"
          fill="#fff"
        />
        <path
          d="M17 4.6 28.6 8.2v10c0 7-4.8 12.6-11.6 15.2C10.2 30.8 5.4 25.2 5.4 18.2v-10L17 4.6Z"
          fill="#00356b"
        />
        <text
          x="17"
          y="23.5"
          textAnchor="middle"
          fontFamily="Open Sans Variable, Open Sans, sans-serif"
          fontWeight="800"
          fontSize="11.5"
          letterSpacing="0.4"
          fill="#fff"
        >
          CC
        </text>
      </svg>
      <span className="brand-name">
        <strong>CAMPUS CUSTOMS</strong>
        <small>NEW HAVEN · YALE GEAR</small>
      </span>
    </Link>
  );
}
