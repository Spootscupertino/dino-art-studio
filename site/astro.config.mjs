// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readFile, writeFile } from 'node:fs/promises';

const SITE = 'https://jurassinkart.com';

/**
 * @astrojs/sitemap generates sitemap-index.xml but only lists its own
 * page sitemap (sitemap-0.xml). Our custom image sitemap
 * (src/pages/sitemap-images.xml.ts) is exposed via robots.txt, but Google
 * discovers sitemaps more reliably from the index. This integration runs
 * AFTER sitemap() in astro:build:done and injects the image sitemap into
 * the already-generated index file.
 */
function imageSitemapInIndex() {
  return {
    name: 'image-sitemap-in-index',
    hooks: {
      'astro:build:done': async ({ dir, logger }) => {
        const indexPath = new URL('sitemap-index.xml', dir);
        try {
          let xml = await readFile(indexPath, 'utf-8');
          if (!xml.includes('/sitemap-images.xml')) {
            const entry = `<sitemap><loc>${SITE}/sitemap-images.xml</loc></sitemap>`;
            xml = xml.replace('</sitemapindex>', `${entry}</sitemapindex>`);
            await writeFile(indexPath, xml, 'utf-8');
            logger.info('Added sitemap-images.xml to sitemap-index.xml');
          }
        } catch (err) {
          logger.warn(`Could not patch sitemap-index.xml: ${err.message}`);
        }
      },
    },
  };
}

export default defineConfig({
  site: SITE,
  // Order matters: imageSitemapInIndex must run after sitemap() so the
  // sitemap-index.xml file already exists when we patch it.
  integrations: [sitemap(), imageSitemapInIndex()],
});
