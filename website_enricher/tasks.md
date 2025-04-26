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

---

# Feature: YAML Config Support & CLI Argument Improvements

## Description
Add support for reading configuration from YAML files (e.g., @dogtolib.yaml) in addition to the current JSON config (which remains as legacy). Refactor CLI argument for blog content source from ambiguous names (like --csv) to --blogs-repo for clarity and future flexibility.

## Requirements Analysis
- Support config files in YAML format (e.g., dogtolib.yaml) using js-yaml.
- Maintain backward compatibility with JSON config files.
- Update CLI argument for blog source to --blogs-repo.
- Update documentation and help output to reflect new options.
- Refactor config loading logic into a dedicated module (config.js).
- Add validation and clear error messages for config loading.
- Add tests for config loading and CLI argument parsing.

## Components Affected
- enrich-webflow-export.js (CLI entrypoint)
- config.js (new or updated module for config loading)
- posts.js, utils.js (if they read config directly)
- Documentation (README, CLI help, code comments)
- Test files (if present)

## Implementation Steps
1. Add YAML config file support (with fallback to JSON)
2. Refactor CLI argument names for blog source to --blogs-repo
3. Refactor config loading logic and documentation
4. Add/Update tests for config and CLI
5. Update README and CLI help output

## Challenges & Mitigations
- Breaking existing workflows using JSON or old argument names: maintain backward compatibility and provide clear migration documentation.
- YAML parsing errors or schema mismatches: add validation and user-friendly error messages.

## Checklist
- [x] Add YAML config file support (with fallback to JSON)
- [ ] Refactor CLI argument names for blog source to --blogs-repo
- [x] Update config loading logic and documentation
- [ ] Add/Update tests for config and CLI
- [x] Update README and CLI help output

## Easy Improvements
- Modularize config loading for easier future extension (e.g., TOML, ENV).
- Add example config files (YAML/JSON) to the repo.
- Use descriptive CLI argument names and provide examples in help output.
- Add a --config argument to specify config file path/type explicitly.

---