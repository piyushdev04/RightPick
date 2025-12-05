import { useEffect, useState } from "react";
import { fetchProducts } from "../api.js";
import ProductCard from "../components/ProductCard.jsx";

function HomePage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        setLoading(true);
        const data = await fetchProducts();
        if (!active) return;
        setProducts(data.items || []);
      } catch (err) {
        console.error(err);
        setError("Failed to load products.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>All Products</h1>
          <p className="page-subtitle">
            Browse all scraped Hunnit products. Click an item to see more details.
          </p>
        </div>
      </header>

      {loading && <p>Loading products…</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
          {products.length === 0 && <p>No products found. Try running /scrape/run.</p>}
        </div>
      )}
    </section>
  );
}

export default HomePage;


