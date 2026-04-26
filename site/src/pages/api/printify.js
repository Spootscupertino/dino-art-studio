export async function GET() {
  const apiKey = import.meta.env.PRINTIFY_API_KEY;
  const configuredShopId = import.meta.env.PRINTIFY_SHOP_ID;

  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'Missing PRINTIFY_API_KEY in .env' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  let shopId = configuredShopId;

  if (!shopId) {
    const shopsResponse = await fetch('https://api.printify.com/v1/shops.json', {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });

    if (!shopsResponse.ok) {
      const details = await shopsResponse.text();
      return new Response(JSON.stringify({
        error: 'Failed to fetch shops from Printify',
        status: shopsResponse.status,
        details
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const shops = await shopsResponse.json();
    shopId = shops?.[0]?.id ? String(shops[0].id) : null;

    if (!shopId) {
      return new Response(JSON.stringify({
        error: 'No shops found for this Printify account. Set PRINTIFY_SHOP_ID in .env if needed.'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  const response = await fetch(`https://api.printify.com/v1/shops/${shopId}/products.json?limit=50`, {
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  });

  if (!response.ok) {
    const details = await response.text();
    return new Response(JSON.stringify({
      error: 'Failed to fetch products from Printify',
      shopId,
      status: response.status,
      details
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  const data = await response.json();
  
  const simplified = (data.data || []).map((product) => ({
    id: product.id,
    title: product.title,
    description: product.description,
    image: product.images?.[0]?.src || null
  }));

  return new Response(JSON.stringify(simplified, null, 2), {
    headers: { 'Content-Type': 'application/json' }
  });
}
