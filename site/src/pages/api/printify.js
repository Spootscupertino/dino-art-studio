export async function GET() {
  const SHOP_ID = '26693677';
  
  const response = await fetch(`https://api.printify.com/v1/shops/${SHOP_ID}/products.json?limit=50`, {
    headers: {
      'Authorization': `Bearer ${import.meta.env.PRINTIFY_API_KEY}`
    }
  });

  if (!response.ok) {
    return new Response(JSON.stringify({ error: 'Failed to fetch' }), { status: 500 });
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
