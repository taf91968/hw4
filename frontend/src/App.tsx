import { Route, Routes, useLocation } from "react-router-dom";
import NavBar from "./components/NavBar";
import Footer from "./components/Footer";
import ChatWidget from "./components/ChatWidget";
import ChatResults from "./components/ChatResults";
import ScrollToTop from "./components/ScrollToTop";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductPage from "./pages/ProductPage";
import About from "./pages/About";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";
import NotFound from "./pages/NotFound";

export default function App() {
  const { pathname } = useLocation();
  return (
    <>
      <ScrollToTop />
      <NavBar />
      <main className="page">
        <ChatResults />
        {/* Keyed by path so each page fades in when the shopper navigates. */}
        <div className="route" key={pathname}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:productId" element={<ProductPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/create-account" element={<CreateAccount />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </main>
      <Footer />
      <ChatWidget />
    </>
  );
}
