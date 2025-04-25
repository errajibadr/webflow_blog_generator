# Task: Refactor enrich-webflow-export.js for Cleanliness and Maintainability

## Description
Refactor the main enrich-webflow-export.js script to be modular, clean, and easily updatable. Move all business logic and helpers to appropriate modules, leaving the entrypoint minimal. Ensure all features and CLI compatibility are preserved.

## Complexity
Level: 3
Type: Feature Refactor

## Technology Stack
- Language: Node.js (JavaScript)
- CLI: yargs
- Templating: Handlebars
- Utilities: fs-extra, path, csv-parse, cheerio

## Technology Validation Checkpoints
- [x] Project initialization command verified
- [x] Required dependencies identified and installed
- [x] Build configuration validated
- [x] Hello world verification completed
- [x] Test build passes successfully

## Status
- [x] Initialization complete
- [x] Planning complete
- [ ] Technology validation complete
- [ ] Implementation steps

## Implementation Plan (Detailed Steps)
Move Helpers to Modules
[x] Move incrementHeadingLevels and processArticleContent to utils.js. All usages updated to use the new helpers with explicit arguments.
[x] Ensure all post reading/processing uses posts.js and utils.js only for these helpers.
Create/Refactor Blog Logic Module
[x] Move blog listing and post generation logic to a new blog.js module. generateBlogListing and generateBlogPosts are now in blog.js and all usages updated.
[x] Export generateBlogListing and generateBlogPosts from blog.js.
Minimize CLI Entrypoint
[x] Refactor enrich-webflow-export.js to only parse CLI args and call a main function. enrich-webflow-export.js is now a minimal CLI entrypoint and all orchestration is done via modules.
[ ] Main function should orchestrate using modules only.
Testing & Documentation
[ ] Test all scenarios.
[ ] Update documentation and code comments.

## Creative Phases Required
- [ ] UI/UX Design
- [x] Architecture Design
- [ ] Algorithm Design

## Dependencies
- fs-extra, path, csv-parse/sync, yargs, cheerio, handlebars
- Internal modules: utils.js, images.js, posts.js, assets.js, templates.js, sitemap.js, htaccess.js

## Challenges & Mitigations
- Ensuring no feature regressions during refactor: Incremental refactor, with tests after each phase
- Avoiding circular dependencies between modules: Careful module boundary planning
- Maintaining CLI compatibility: Do not change argument parsing or output structure

## Requirements
- [x] Refactor enrich-webflow-export.js to be clean, modular, and easily updatable
- [x] Eliminate code duplication and move logic to appropriate modules
- [x] Ensure all business logic is in reusable, testable functions
- [x] CLI entrypoint should be minimal, delegating to modules
- [x] Maintain all current features and output

## Components Affected
- enrich-webflow-export.js
- posts.js
- utils.js
- images.js
- templates.js
- assets.js
- sitemap.js
- htaccess.js

## Implementation Steps
1. Move helpers to modules
2. Refactor blog logic to new module
3. Minimize CLI entrypoint
4. Test and document

## Creative Phases Required
- [ ] 🎨 UI/UX Design
- [x] 🏗️ Architecture Design
- [ ] ⚙️ Algorithm Design

## Checkpoints
- [ ] Requirements verified
- [ ] Creative phases completed
- [ ] Implementation tested
- [ ] Documentation updated

## Current Status
- Phase: Planning
- Status: In Progress
- Blockers: None 