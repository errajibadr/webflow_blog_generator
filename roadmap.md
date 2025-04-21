# Roadmap & Architecture Notes

## JSON-LD Injection for Blog Articles (2025-04-21)

- Blog article JSON files now include a `JSON_LD` field (stringified JSON array of BlogPosting, FAQ, HowTo, etc.).
- During enrichment (Node.js: enrich-webflow-export.js):
  - For each blog post, if `JSON_LD` is present:
    - Parse the string as JSON.
    - Replace `{author}` with the actual author name (from post or config).
    - Replace `{main_entity_of_page}` with the canonical URL for the post.
    - Re-stringify the array and inject as a `<script type="application/ld+json">` in the blog post HTML `<head>`.
- The Handlebars template (`blog-post.html`) uses `{{{json_ld_script}}}` to inject the raw JSON-LD script (no escaping).
- This ensures correct SEO structured data for each blog post, with dynamic values and support for multiple schema types.

---

(Keep this section updated as the enrichment/data pipeline evolves.) 