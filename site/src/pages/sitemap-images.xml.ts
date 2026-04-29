import type { APIRoute } from 'astro';
import { getImage } from 'astro:assets';
import productsData from '../data/products.json';

const SITE = 'https://jurassinkart.com';

const imageModules = import.meta.glob<{ default: ImageMetadata }>(
  '../assets/gallery/**/*.{png,jpg,jpeg,webp,gif}',
  { eager: true }
);

// Key by "<category>/<basename>" to match the relative path stored in products.json.
const byFilename = new Map<string, ImageMetadata>();
for (const [path, mod] of Object.entries(imageModules)) {
  const parts = path.split('/');
  const relPath = parts.slice(-2).join('/');
  byFilename.set(relPath, mod.default);
}

function escapeXml(s: string): string {
  return s.replace(/[<>&'"]/g, (c) =>
    ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' }[c]!)
  );
}

export const GET: APIRoute = async () => {
  const entries = await Promise.all(
    productsData
      .filter((p) => p.type !== 'video')
      .map(async (p) => {
        const asset = byFilename.get(p.filename);
        if (!asset) return null;
        const full = await getImage({
          src: asset,
          format: 'webp',
          width: Math.min(p.width, 2400),
          quality: 88,
        });
        return {
          loc: `${SITE}${full.src}`,
          title: `${p.title} — ${p.scientific_name}`,
          caption: p.alt,
        };
      })
  );

  const images = entries
    .filter((e): e is NonNullable<typeof e> => e !== null)
    .map(
      (e) => `    <image:image>
      <image:loc>${escapeXml(e.loc)}</image:loc>
      <image:title>${escapeXml(e.title)}</image:title>
      <image:caption>${escapeXml(e.caption)}</image:caption>
    </image:image>`
    )
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>${SITE}/</loc>
${images}
  </url>
</urlset>
`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
