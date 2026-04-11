import { redisGetInt, redisGet, redisSet } from '../config/redis.js';

/**
 * Fetch competitor price with 15-minute Redis caching.
 * Real marketplace APIs are slow, so we cache a derived price.
 */
async function getCompetitorPrice(productId, basePrice) {
  const cacheKey = `comp:price:${productId}`;
  const cached = await redisGet(cacheKey);
  if (cached) return parseFloat(cached);

  // Simulated lookup: Competitors are typically 2-8% within our price
  // For a "match" scenario, we target slightly below them.
  const compPrice = basePrice * (0.95 + Math.random() * 0.1);
  await redisSet(cacheKey, compPrice.toString(), 15 * 60); // 15 min TTL
  return compPrice;
}

/**
 * Compute user segment from session object.
 * Uses ONLY non-discriminatory behavioral/commercial signals.
 */
export function computeUserSegment(session = {}) {
  const eng = session.engagementScore || 0;
  const intent = session.purchaseIntentScore || 0;
  const affinity = session.categoryAffinity || {};
  const electronicsAff = (affinity instanceof Map ? affinity.get('Electronics') : affinity['Electronics']) || 0;

  if (eng > 15 || electronicsAff > 5) return 'premium_intent';
  if (intent < 0.2 && eng < 5) return 'value_seeker';
  return 'standard';
}

/**
 * Dynamic pricing engine.
 */
export function calculate(product, sessionData = {}, recentViews = 0, competitorPrice = null) {
  let price = product.basePrice;
  let reason = 'Standard Price';
  const segment = sessionData.userSegment || 'standard';

  // Rule 1 — Inventory Scarcity vs Restock Timeline
  const restockDays = product.restockDays || 7;
  if (product.stock <= 3 && restockDays > 7) {
    price = product.basePrice * 1.20; // +20% high scarcity
    reason = 'Limited Stock';
  } else if (product.stock <= 5) {
    price = price * 1.12; 
    reason = 'Limited Stock';
  }

  // Rule 2 — High Demand (views in last 15 min)
  if (recentViews >= 30) {
    price = Math.max(price, product.basePrice * 1.15);
    reason = 'High Demand';
  } else if (recentViews >= 15) {
    price = Math.max(price, product.basePrice * 1.08);
    reason = 'High Demand';
  }

  // Rule 3 — A/B Variant: control gets flat base price
  if (sessionData.abVariant === 'control') {
    price = product.basePrice;
    reason = 'Standard Price';
  }

  // Rule 4 — Competitor Price Match (Treatment only)
  if (sessionData.abVariant !== 'control' && competitorPrice) {
    const targetPrice = competitorPrice * 0.95; // 5% discount on competitor
    if (targetPrice < price) {
      price = targetPrice;
      reason = 'Competitor Match';
    }
  }

  // Rule 5 — Behavioral Surge (Low stock + high demand)
  if (product.stock <= 3 && recentViews >= 20 && sessionData.abVariant !== 'control') {
    price = product.basePrice * 1.22;
    reason = 'Limited Stock';
  }

  // Rule 6 — User Willingness-to-Pay (Value Seeker fallback)
  if (segment === 'value_seeker' && sessionData.abVariant !== 'control' && reason === 'Standard Price') {
    price = price * 0.97;
  }

  // Enforcement: Floor (70% MRP) | Ceiling (100% MRP)
  price = Math.max(price, product.mrp * 0.7);
  price = Math.min(price, product.mrp);
  price = Math.round(price);

  const discount = Math.round(((product.mrp - price) / product.mrp) * 100);

  return { price, reason, discount, userSegment: segment };
}

/**
 * Convenience: get recentViews and competitorPrice then calculate.
 */
export async function calculateWithRedis(product, sessionData = {}) {
  const [recentViews, competitorPrice] = await Promise.all([
    redisGetInt(`views:15m:${product.id}`),
    getCompetitorPrice(product.id, product.basePrice)
  ]);
  
  // Attempt to use ML service for A/B Treatment
  if (sessionData.abVariant !== 'control') {
    try {
      const mlUrl = process.env.ML_SERVICE_URL || 'http://localhost:8000';
      const userSegment = sessionData.userSegment || 'standard';
      const demandScore = Math.min(recentViews || 0, 50) / 50.0;
      const mlRes = await fetch(
        `${mlUrl}/price-predict?product_id=${product.id}&demand_score=${demandScore}&stock=${product.stock || 100}&user_segment=${userSegment}`,
        { signal: AbortSignal.timeout(1000) }
      );
      
      if (mlRes.ok) {
        const mlData = await mlRes.json();
        if (mlData && typeof mlData.uplift_factor === 'number') {
          let price = product.basePrice * (1 + mlData.uplift_factor);
          
          // Apply competitor matching logic if necessary
          if (competitorPrice) {
            const targetPrice = competitorPrice * 0.95;
            if (targetPrice < price) {
               // We might choose to still undercut competitor slightly
               price = targetPrice;
               mlData.price_reason = 'Competitor Match';
            }
          }

          // Enforcement bounds
          price = Math.max(price, product.mrp * 0.7);
          price = Math.min(price, product.mrp);
          price = Math.round(price);
          
          const discount = Math.round(((product.mrp - price) / product.mrp) * 100);
          
          return {
            price,
            reason: mlData.price_reason || 'ai_dynamic_pricing',
            discount,
            userSegment,
            model: mlData.model
          };
        }
      }
    } catch (err) {
      console.warn(`ML pricing service unreachable for product ${product.id}, falling back:`, err.message);
    }
  }

  // Fallback to local rule-based pricing
  return calculate(product, sessionData, recentViews, competitorPrice);
}
