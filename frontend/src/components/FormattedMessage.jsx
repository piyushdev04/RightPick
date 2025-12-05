import { Link } from "react-router-dom";

function FormattedMessage({ content, products = [] }) {
  // Safety check
  if (!content || typeof content !== "string") {
    return <div className="formatted-message">{String(content || "")}</div>;
  }

  // Helper to find product by title (fuzzy match)
  const findProduct = (title) => {
    if (!title || !products.length) return null;
    const titleLower = title.toLowerCase().trim();
    // Remove common prefixes/suffixes
    const cleanTitle = titleLower
      .replace(/^(the|a|an)\s+/i, "")
      .replace(/\s*\([^)]*\)/g, "")
      .trim();

    // Try exact match first
    let match = products.find((p) => {
      const pTitle = p.title.toLowerCase();
      return pTitle === titleLower || pTitle === cleanTitle;
    });
    if (match) return match;

    // Try partial match with key words
    const keyWords = cleanTitle.split(/\s+/).filter((w) => w.length > 3);
    match = products.find((p) => {
      const pTitle = p.title.toLowerCase();
      // Check if at least 2 key words match
      const matches = keyWords.filter((kw) => pTitle.includes(kw));
      return matches.length >= Math.min(2, keyWords.length);
    });
    if (match) return match;

    // Fallback: single key word match
    return products.find((p) => {
      const pTitle = p.title.toLowerCase();
      return keyWords.some((kw) => pTitle.includes(kw));
    });
  };

  // Parse markdown-style links and bold text
  const parseContent = (text) => {
    if (!text || typeof text !== "string") {
      return [{ type: "text", content: String(text || "") }];
    }
    const parts = [];
    let lastIndex = 0;

    // Match **bold** text and [link text](url)
    const patterns = [
      { regex: /\*\*([^*]+)\*\*/g, type: "bold" },
      { regex: /\[([^\]]+)\]\(([^)]+)\)/g, type: "link" },
    ];

    const matches = [];
    patterns.forEach(({ regex, type }) => {
      let match;
      while ((match = regex.exec(text)) !== null) {
        matches.push({
          index: match.index,
          type,
          content: match[1],
          url: match[2] || null,
          fullMatch: match[0], // Store the full matched string
        });
      }
    });

    matches.sort((a, b) => a.index - b.index);

    matches.forEach((match) => {
      if (match.index > lastIndex) {
        parts.push({ type: "text", content: text.slice(lastIndex, match.index) });
      }
      parts.push(match);
      lastIndex = match.index + match.fullMatch.length;
    });

    if (lastIndex < text.length) {
      parts.push({ type: "text", content: text.slice(lastIndex) });
    }

    return parts.length > 0 ? parts : [{ type: "text", content: text }];
  };

  // Extract product recommendations (look for patterns like "Product Name (₹price)" or **Product Name** (₹price))
  const extractRecommendations = (text) => {
    const recommendations = [];
    // Pattern 1: **Product Name** (₹price) or Product Name (₹price)
    const productPattern1 = /(?:\*\*)?([^*\n]+?)(?:\*\*)?\s*\(₹([\d.]+)\)/g;
    let match;
    while ((match = productPattern1.exec(text)) !== null) {
      const title = match[1].trim().replace(/\[([^\]]+)\]\([^)]+\)/g, "$1"); // Remove markdown links
      const price = match[2];
      const product = findProduct(title);
      if (product || title.length > 5) {
        recommendations.push({
          title,
          price: parseFloat(price),
          product: product || null,
        });
      }
    }

    // Pattern 2: **Product Name** followed by price elsewhere (₹price)
    const boldPattern = /\*\*([^*\n]+?)\*\*/g;
    const pricePattern = /₹([\d.]+)/g;
    const boldMatches = Array.from(text.matchAll(boldPattern));
    const priceMatches = Array.from(text.matchAll(pricePattern));

    boldMatches.forEach((boldMatch, idx) => {
      const title = boldMatch[1].trim().replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
      // Find nearest price after this bold text
      const boldIndex = boldMatch.index;
      const nearestPrice = priceMatches.find((pm) => pm.index > boldIndex && pm.index < boldIndex + 200);
      if (nearestPrice && title.length > 5) {
        const existing = recommendations.find((r) => r.title.toLowerCase() === title.toLowerCase());
        if (!existing) {
          const product = findProduct(title);
          recommendations.push({
            title,
            price: parseFloat(nearestPrice[1]),
            product: product || null,
          });
        }
      }
    });

    return recommendations;
  };

  const recommendations = extractRecommendations(content);
  const hasRecommendations = recommendations.length > 0;

  // If we have structured recommendations, render them nicely
  if (hasRecommendations) {
    const parts = parseContent(content);
    const introText = parts
      .filter((p) => p.type === "text" && !p.content.match(/₹[\d.]+/))
      .map((p) => p.content)
      .join("")
      .trim();

    return (
      <div className="formatted-message">
        {introText && (
          <div className="message-intro">
            {parts
              .filter((p) => p.type === "text" && !p.content.match(/₹[\d.]+/))
              .map((p, i) => {
                if (p.content.trim().length === 0) return null;
                return <p key={i}>{p.content.trim()}</p>;
              })}
          </div>
        )}

        <div className="recommendations-grid">
          {recommendations.map((rec, idx) => (
            <div key={idx} className="recommendation-card">
              <div className="rec-header">
                <span className="rec-number">{idx + 1}️⃣</span>
                <h4 className="rec-title">{rec.title}</h4>
              </div>
              <div className="rec-price">₹{rec.price.toLocaleString()}</div>
              {rec.product && (
                <>
                  {rec.product.activities && rec.product.activities.length > 0 && (
                    <div className="rec-features">
                      {rec.product.activities.slice(0, 3).map((act, i) => (
                        <span key={i} className="rec-tag">
                          ✔ {act}
                        </span>
                      ))}
                    </div>
                  )}
                  <Link to={`/products/${rec.product.id}`} className="rec-link">
                    View Product →
                  </Link>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Render any remaining text/links */}
        {parts
          .filter((p) => p.type === "link" || (p.type === "text" && p.content.match(/₹[\d.]+/)))
          .map((p, i) => {
            if (p.type === "link") {
              return (
                <a key={i} href={p.url} target="_blank" rel="noopener noreferrer" className="message-link">
                  {p.content}
                </a>
              );
            }
            return null;
          })}
      </div>
    );
  }

  // Fallback: render as regular formatted text
  const parts = parseContent(content);
  return (
    <div className="formatted-message">
      {parts.map((part, i) => {
        if (part.type === "text") {
          // Split by newlines and render paragraphs
          const paragraphs = part.content.split(/\n\n/);
          return (
            <div key={i}>
              {paragraphs.map((para, j) => (
                <p key={j}>{para.trim() || <br />}</p>
              ))}
            </div>
          );
        }
        if (part.type === "bold") {
          return <strong key={i}>{part.content}</strong>;
        }
        if (part.type === "link") {
          return (
            <a key={i} href={part.url} target="_blank" rel="noopener noreferrer" className="message-link">
              {part.content}
            </a>
          );
        }
        return null;
      })}
    </div>
  );
}

export default FormattedMessage;

