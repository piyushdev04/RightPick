import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchProduct } from "../api.js";

function ProductPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        setLoading(true);
        const data = await fetchProduct(id);
        if (!active) return;
        setProduct(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load product.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) return <p>Loading product…</p>;
  if (error) return <p className="error-text">{error}</p>;
  if (!product) return <p>Product not found.</p>;

  const activities = product.activities || [];

  return (
    <section className="product-detail">
      <header className="page-header">
        <div>
          <h1>{product.title}</h1>
          <p className="page-subtitle">
            {product.category && <span className="product-pill">{product.category}</span>}
          </p>
        </div>
        <Link to="/" className="btn-secondary">
          ← Back to products
        </Link>
      </header>

      <div className="product-detail-layout">
        <div className="product-detail-image">
          {product.image_url ? (
            <img src={product.image_url} alt={product.title} />
          ) : (
            <div className="placeholder-image">No image</div>
          )}
        </div>

        <div className="product-detail-info">
          <p className="product-detail-price">
            {product.price ? `₹${product.price.toFixed(0)}` : "Price unavailable"}
          </p>

          {product.description && (
            <div className="product-detail-section">
              <h3>Description</h3>
              <p>{product.description.replace(/<[^>]+>/g, "")}</p>
            </div>
          )}

          {product.features && (
            <div className="product-detail-section">
              <h3>Features</h3>
              <pre className="product-features">{product.features}</pre>
            </div>
          )}

          {activities.length > 0 && (
            <div className="product-detail-section">
              <h3>Best for</h3>
              <div className="pill-row">
                {activities.map((a) => (
                  <span key={a} className="product-pill">
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="product-detail-section">
            <a
              href={product.product_url}
              className="btn-primary"
              target="_blank"
              rel="noreferrer"
            >
              View on Hunnit.com
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ProductPage;


