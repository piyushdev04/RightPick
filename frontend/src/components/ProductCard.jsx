import { Link } from "react-router-dom";

function ProductCard({ product }) {
  return (
    <Link to={`/products/${product.id}`} className="product-card">
      <div className="product-image-wrapper">
        {product.image_url ? (
          <img src={product.image_url} alt={product.title} />
        ) : (
          <div className="placeholder-image">No image</div>
        )}
      </div>
      <div className="product-body">
        <h3 className="product-title">{product.title}</h3>
        <p className="product-price">
          {product.price ? `₹${product.price.toFixed(0)}` : "Price unavailable"}
        </p>
        {product.category && (
          <span className="product-pill">{product.category}</span>
        )}
      </div>
    </Link>
  );
}

export default ProductCard;


