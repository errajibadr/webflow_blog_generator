# 🎨🎨🎨 ENTERING CREATIVE PHASE: UI/UX DESIGN 🎨🎨🎨

Focus: Command-line interface and output formatting for Website SEO Orchestrator
Objective: Design an intuitive CLI experience with clear, informative output that helps users understand system status and troubleshoot issues
Requirements:
- Create an intuitive argument structure for command-line use
- Design clear, color-coded console output for status and errors
- Develop progress indicators for long-running operations
- Create formatted output for logs and reports
- Support both normal and verbose output modes

## Context

### System Requirements
- Command-line interface for orchestrating website SEO operations
- Support for multiple websites with different configurations
- Detailed logging and error handling
- Dry-run capability for testing without making changes
- Progress tracking for long-running operations

### Technical Constraints
- Must work with Python's argparse for CLI arguments
- Must support color output in terminals that support it
- Must fallback gracefully in environments without color support
- Must provide both human-readable and log-friendly output formats
- Should follow CLI best practices and conventions

## UI Analysis

### User Types and Needs
- **Regular Users**: Need clear instructions, progress updates, and success/failure indications
- **Technical Users**: Need detailed output, error information, and debugging capabilities
- **Automated Systems**: Need structured output that can be parsed by scripts or monitoring tools

### Key User Journeys
1. First-time setup and configuration
2. Regular content generation workflow
3. Troubleshooting failed operations
4. Monitoring progress of long-running tasks
5. Testing changes with dry-run mode

### UI Elements Required
- Command-line argument parser
- Help text and documentation
- Progress indicators
- Status messages
- Error messages and warnings
- Summary reports
- Log output formatting

## Design Options

### Option 1: Traditional CLI with Simple Output

#### Description
A traditional command-line interface with simple, text-based output using minimal formatting and color. Focus on clarity and simplicity.

#### Example Output
```
$ python main.py --website example --export --generate
[INFO] Starting export for website: example
[INFO] Exported 157 files to workspaces/example/export
[INFO] Starting content generation for website: example
[INFO] Generated 12 content items
[INFO] All operations completed successfully
```

#### Pros
- Simple and straightforward
- Works in all terminal environments
- Easy to parse by scripts
- Minimal dependencies
- Familiar to most users

#### Cons
- Limited visual hierarchy
- Harder to distinguish different types of information
- Less engaging user experience
- Difficult to show progress for long operations
- Limited ability to emphasize important information

#### Technical Fit: High
#### Usability: Medium
#### Scalability: Medium

### Option 2: Rich Interactive CLI

#### Description
A modern, interactive CLI with rich formatting, colors, progress bars, and interactive elements using libraries like rich, tqdm, or click.

#### Example Output
```
$ python main.py --website example --export --generate
✨ Website SEO Orchestrator ✨

🔄 Exporting website: example
[■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100% | 157 files | 3.2s
✅ Export complete!

🔄 Generating content
[■■■■■■■■■■■■■■■■■■■--------] 60% | 7/12 items | ETA: 2m15s
```

#### Pros
- Visually engaging and modern
- Clear visual hierarchy with colors and formatting
- Real-time progress updates
- Better emphasis on important information
- Improved user experience

#### Cons
- May not work in all terminal environments
- More dependencies
- More complex implementation
- Could be overwhelming with too much formatting
- May interfere with log parsing in automated environments

#### Technical Fit: Medium
#### Usability: High
#### Scalability: Medium

### Option 3: Hybrid Approach with Output Modes

#### Description
A flexible CLI that supports multiple output modes (normal, verbose, quiet, json) with appropriate formatting for each context, using conditional formatting and structured data.

#### Example Output - Normal Mode
```
$ python main.py --website example --export --generate
[INFO] Starting website processing for: example
[EXPORT] ████████████████████████████ 100% | 3.2s
[CONTENT] ██████████████░░░░░░░░░░░░░ 60% | ETA: 2m15s
```

#### Example Output - Verbose Mode
```
$ python main.py --website example --export --generate --verbose
[2023-04-01 12:34:56] [INFO] Configuring for website: example
[2023-04-01 12:34:56] [INFO] Using config from: website_configs/example.yaml
[2023-04-01 12:34:56] [INFO] Workspace path: workspaces/example
[2023-04-01 12:34:56] [INFO] Starting export process
[2023-04-01 12:34:57] [DEBUG] Connecting to Hostinger API
[2023-04-01 12:34:58] [INFO] Authenticated successfully
[2023-04-01 12:34:59] [INFO] Downloading files (157 total)
...
```

#### Example Output - JSON Mode
```
$ python main.py --website example --export --generate --json
{
  "status": "in_progress",
  "website": "example",
  "operations": [
    {
      "type": "export",
      "status": "completed",
      "files_count": 157,
      "duration_seconds": 3.2
    },
    {
      "type": "generate",
      "status": "in_progress",
      "items_completed": 7,
      "items_total": 12,
      "eta_seconds": 135
    }
  ]
}
```

#### Pros
- Adaptable to different user needs and contexts
- Provides appropriate detail level for each use case
- Supports both human and machine consumption
- Balances visual appeal with functionality
- Scales well with increasing complexity

#### Cons
- More complex implementation
- More configuration options to manage
- May require learning different output modes
- Consistency challenges across modes
- Slightly increased development effort

#### Technical Fit: High
#### Usability: High
#### Scalability: High

### Option 4: Component-Based Console UI

#### Description
A modular, component-based approach to console UI with reusable UI components like progress bars, tables, error displays, and banners that can be composed for different operations.

#### Example Output
```
$ python main.py --website example --all
┌─────────────────────────────────────────────────────┐
│                Website SEO Orchestrator              │
│                   Website: example                   │
└─────────────────────────────────────────────────────┘

┌─ EXPORT ───────────────────────────────────────────┐
│ [■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100% | 157 files    │
│ Duration: 3.2s | Status: ✅ Completed               │
└─────────────────────────────────────────────────────┘

┌─ CONTENT GENERATION ──────────────────────────────┐
│ [■■■■■■■■■■■■■■■■■■--------] 60% | 7/12 items     │
│ ETA: 2m15s | Status: 🔄 In Progress               │
└─────────────────────────────────────────────────────┘
```

#### Pros
- Consistent visual language across the application
- Reusable components reduce duplication
- Clear organization of information
- Scalable to complex operations
- Visually appealing and professional

#### Cons
- Most complex implementation
- Higher dependency footprint
- Potential performance impact with heavy formatting
- May not work well in all terminal environments
- Overkill for simple operations

#### Technical Fit: Medium
#### Usability: High
#### Scalability: High

## Decision

### Chosen Option: Hybrid Approach with Output Modes

#### Rationale
The Hybrid Approach with Output Modes provides the best balance of flexibility, usability, and technical fit for the Website SEO Orchestrator. It addresses diverse user needs by offering appropriate levels of detail and formatting for different contexts, while maintaining compatibility with various environments.

This approach addresses the key requirements:
- **Intuitive Argument Structure**: Clean command structure with mode-specific options
- **Color-Coded Output**: Available in normal mode, but optional
- **Progress Indicators**: Visual in normal mode, detailed in verbose mode
- **Formatted Output**: Structured appropriately for each output mode
- **Support for Different Modes**: Normal, verbose, quiet, and JSON modes

### Implementation Considerations

#### Command-Line Argument Structure
```python
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Website SEO Orchestrator - Manage website content generation and deployment"
    )
    
    # Website selection
    parser.add_argument(
        "--website", "-w",
        required=True,
        help="Name of the website to process (must have a config in website_configs/)"
    )
    
    # Operation flags
    operation_group = parser.add_argument_group("operations")
    operation_group.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run the complete pipeline (export, generate, enrich, import)"
    )
    operation_group.add_argument(
        "--export", "-e",
        action="store_true",
        help="Export website from hosting provider"
    )
    operation_group.add_argument(
        "--generate", "-g",
        action="store_true",
        help="Generate SEO content"
    )
    operation_group.add_argument(
        "--enrich", "-r",
        action="store_true",
        help="Enrich website with generated content"
    )
    operation_group.add_argument(
        "--import", "-i",
        dest="import_website",  # Avoid keyword clash
        action="store_true",
        help="Import enriched website to hosting provider"
    )
    
    # Output mode options
    output_group = parser.add_argument_group("output options")
    output_mode = output_group.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with detailed information"
    )
    output_mode.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimize output, show only errors and critical information"
    )
    output_mode.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (useful for scripting)"
    )
    
    # Additional options
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Simulate operations without making actual changes"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to global configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--purge-remote",
        action="store_true",
        help="Purge remote website content before importing (use with caution)"
    )
    
    return parser.parse_args()
```

#### Output Manager Class
```python
import json
import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

class OutputMode(Enum):
    """Output modes for the orchestrator."""
    NORMAL = "normal"
    VERBOSE = "verbose"
    QUIET = "quiet"
    JSON = "json"

class OutputManager:
    """Manages console output and formatting."""
    
    def __init__(self, mode: OutputMode = OutputMode.NORMAL, use_color: bool = True):
        self.mode = mode
        self.use_color = use_color and sys.stdout.isatty()
        self.progress_bars = {}
        self.json_data = {"operations": []} if mode == OutputMode.JSON else None
        
        # ANSI color codes
        if self.use_color:
            self.COLORS = {
                "reset": "\033[0m",
                "bold": "\033[1m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m",
                "bg_red": "\033[41m",
                "bg_green": "\033[42m",
            }
        else:
            self.COLORS = {key: "" for key in [
                "reset", "bold", "red", "green", "yellow", "blue", 
                "magenta", "cyan", "white", "bg_red", "bg_green"
            ]}
    
    def info(self, message: str, module: str = None):
        """Display informational message."""
        if self.mode == OutputMode.QUIET:
            return
        
        if self.mode == OutputMode.JSON:
            # Add to JSON data structure if appropriate
            return
            
        if self.mode == OutputMode.VERBOSE:
            prefix = f"[INFO] "
            if module:
                prefix = f"[INFO] [{module}] "
        else:
            prefix = ""
            if module:
                prefix = f"[{module}] "
        
        if module:
            color_prefix = f"{self.COLORS['cyan']}{prefix}{self.COLORS['reset']}"
        else:
            color_prefix = prefix
            
        print(f"{color_prefix}{message}")
    
    def success(self, message: str, module: str = None):
        """Display success message."""
        if self.mode == OutputMode.QUIET:
            return
            
        if self.mode == OutputMode.JSON:
            # Add to JSON data structure if appropriate
            return
            
        if module:
            prefix = f"[{module}] "
        else:
            prefix = ""
            
        print(f"{self.COLORS['green']}✓ {prefix}{message}{self.COLORS['reset']}")
    
    def error(self, message: str, module: str = None):
        """Display error message."""
        if self.mode == OutputMode.JSON:
            # Add error to JSON data structure
            if "errors" not in self.json_data:
                self.json_data["errors"] = []
            self.json_data["errors"].append({
                "message": message,
                "module": module
            })
            return
            
        if module:
            prefix = f"[{module}] "
        else:
            prefix = ""
            
        print(f"{self.COLORS['red']}✗ {prefix}{message}{self.COLORS['reset']}", file=sys.stderr)
    
    def warning(self, message: str, module: str = None):
        """Display warning message."""
        if self.mode == OutputMode.QUIET:
            return
            
        if self.mode == OutputMode.JSON:
            # Add warning to JSON data structure
            if "warnings" not in self.json_data:
                self.json_data["warnings"] = []
            self.json_data["warnings"].append({
                "message": message,
                "module": module
            })
            return
            
        if module:
            prefix = f"[{module}] "
        else:
            prefix = ""
            
        print(f"{self.COLORS['yellow']}! {prefix}{message}{self.COLORS['reset']}")
    
    def create_progress_bar(self, total: int, desc: str, unit: str = "items"):
        """Create a progress bar for tracking operation progress."""
        if self.mode == OutputMode.QUIET or self.mode == OutputMode.JSON:
            return None
            
        if self.mode == OutputMode.VERBOSE:
            # Don't use visual progress bar in verbose mode
            self.info(f"Starting operation: {desc} (total: {total} {unit})")
            return None
            
        if HAS_TQDM:
            progress_bar = tqdm(
                total=total,
                desc=f"{self.COLORS['cyan']}{desc}{self.COLORS['reset']}",
                unit=unit,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit}"
            )
            self.progress_bars[desc] = progress_bar
            return progress_bar
        else:
            # Fallback for environments without tqdm
            self.info(f"Starting: {desc} (0/{total} {unit})")
            return None
    
    def update_progress(self, desc: str, increment: int = 1, message: str = None):
        """Update a progress bar."""
        if self.mode == OutputMode.JSON:
            # Update operation status in JSON data
            for op in self.json_data["operations"]:
                if op.get("description") == desc:
                    op["progress"] += increment
                    break
            return
            
        if desc in self.progress_bars and HAS_TQDM:
            self.progress_bars[desc].update(increment)
            if message and self.mode != OutputMode.QUIET:
                self.progress_bars[desc].write(message)
        elif self.mode == OutputMode.VERBOSE:
            if message:
                self.info(message)
    
    def close_progress(self, desc: str, success: bool = True):
        """Close a progress bar."""
        if desc in self.progress_bars and HAS_TQDM:
            self.progress_bars[desc].close()
            del self.progress_bars[desc]
            
        if success:
            self.success(f"{desc} completed successfully")
        else:
            self.error(f"{desc} failed")
    
    def print_summary(self, operations: List[Dict[str, Any]]):
        """Print operation summary."""
        if self.mode == OutputMode.JSON:
            self.json_data["summary"] = operations
            print(json.dumps(self.json_data, indent=2))
            return
            
        if self.mode == OutputMode.QUIET:
            return
            
        print("\n" + "=" * 60)
        print(f"{self.COLORS['bold']}OPERATION SUMMARY{self.COLORS['reset']}")
        print("=" * 60)
        
        for op in operations:
            status = op.get("status", "unknown")
            if status == "success":
                status_str = f"{self.COLORS['green']}✓ Success{self.COLORS['reset']}"
            elif status == "failure":
                status_str = f"{self.COLORS['red']}✗ Failed{self.COLORS['reset']}"
            elif status == "skipped":
                status_str = f"{self.COLORS['yellow']}⏭ Skipped{self.COLORS['reset']}"
            else:
                status_str = f"{self.COLORS['yellow']}? Unknown{self.COLORS['reset']}"
                
            print(f"{self.COLORS['bold']}{op['name']}{self.COLORS['reset']}: {status_str}")
            if "details" in op and op["details"]:
                print(f"  Details: {op['details']}")
            if "duration" in op:
                print(f"  Duration: {op['duration']:.2f}s")
            print("-" * 60)
        
        print("")
```

#### Dry Run Display
```python
def display_dry_run_info(output_manager, operation, website, details=None):
    """Display information about dry run operation."""
    output_manager.info(f"DRY RUN: Would {operation} website '{website}'")
    
    if details and isinstance(details, dict):
        if output_manager.mode == OutputMode.VERBOSE:
            for key, value in details.items():
                output_manager.info(f"  {key}: {value}")
        elif output_manager.mode == OutputMode.NORMAL:
            # Show simplified details in normal mode
            for key, value in details.items():
                if key in ["count", "duration", "size"]:
                    output_manager.info(f"  {key}: {value}")
```

#### Usage Examples
```python
def run_export(config, website_name, dry_run=False):
    """Run the export step."""
    output = config.get("output_manager")
    
    if dry_run:
        display_dry_run_info(output, "export", website_name, {
            "estimated_files": 150,
            "estimated_duration": "30 seconds"
        })
        return True
    
    try:
        output.info(f"Starting export process for website: {website_name}", "exporter")
        progress = output.create_progress_bar(0, "Exporting files", "files")
        
        # Initial export setup
        from modules.exporter import export_website
        file_count = export_website(config, website_name, progress_callback=lambda n: 
            output.update_progress("Exporting files", n))
        
        output.close_progress("Exporting files", True)
        output.success(f"Exported {file_count} files successfully", "exporter")
        return True
    except Exception as e:
        output.error(f"Export failed: {str(e)}", "exporter")
        return False
```

## UI/UX Elements

### Color Scheme
- **Informational**: Cyan (`#00FFFF`)
- **Success**: Green (`#00FF00`)
- **Warning**: Yellow (`#FFFF00`)
- **Error**: Red (`#FF0000`)
- **Progress**: Blue (`#0000FF`)
- **Emphasis**: Bold white

### Progress Indicators
- Visual progress bars for normal mode
- Textual progress updates for verbose mode
- Completion summaries for all modes

### Help Text Design
- Command grouped by category
- Concise descriptions
- Examples for common use cases

### Operation Hierarchy
1. Website selection (`--website`)
2. Operation selection (`--export`, `--generate`, etc.)
3. Output mode selection (`--verbose`, `--quiet`, `--json`)
4. Additional options (`--dry-run`, `--config`)

## Validation

### Requirements Met
- [✓] Intuitive argument structure for command-line use
- [✓] Clear, color-coded console output for status and errors
- [✓] Progress indicators for long-running operations
- [✓] Formatted output for logs and reports
- [✓] Support for both normal and verbose output modes

### Technical Feasibility
The proposed UI/UX design is technically feasible and aligns well with Python's capabilities. The implementation uses standard libraries like argparse for argument parsing and can incorporate optional libraries like tqdm for progress bars.

### User Experience Assessment
- **Clarity**: High - Clear presentation of information with visual hierarchy
- **Learnability**: High - Intuitive command structure and consistent patterns
- **Efficiency**: High - Appropriate detail level for different user needs
- **Error Recovery**: High - Clear error messages and helpful suggestions
- **Satisfaction**: Medium-High - Visually appealing when color is supported

🎨 CREATIVE CHECKPOINT: CLI Design
- Progress: Complete
- Decisions: Hybrid approach with multiple output modes
- Next steps: Integrate with module interfaces and error handling

## Help Text Design

```
Usage: main.py --website WEBSITE [operations] [output options] [additional options]

Website SEO Orchestrator - Manage website content generation and deployment

required arguments:
  --website WEBSITE, -w WEBSITE
                        Name of the website to process (must have a config in website_configs/)

operations:
  --all, -a             Run the complete pipeline (export, generate, enrich, import)
  --export, -e          Export website from hosting provider
  --generate, -g        Generate SEO content
  --enrich, -r          Enrich website with generated content
  --import, -i          Import enriched website to hosting provider

output options:
  --verbose, -v         Enable verbose output with detailed information
  --quiet, -q           Minimize output, show only errors and critical information
  --json                Output in JSON format (useful for scripting)

additional options:
  --dry-run, -d         Simulate operations without making actual changes
  --config CONFIG, -c CONFIG
                        Path to global configuration file (default: config.yaml)
  --purge-remote        Purge remote website content before importing (use with caution)

examples:
  python main.py --website example --all                   # Run full pipeline
  python main.py --website example --export --generate     # Only export and generate
  python main.py --website example --all --dry-run         # Simulate full pipeline
  python main.py --website example --all --verbose         # Run with detailed output
```

# 🎨🎨🎨 EXITING CREATIVE PHASE 🎨🎨🎨

Summary: Designed a flexible, user-friendly command-line interface with multiple output modes to accommodate different user needs and contexts, providing appropriate levels of detail and visual feedback.

Key Decisions:
- Adopted a hybrid approach with multiple output modes (normal, verbose, quiet, JSON)
- Implemented color-coded output for status and errors
- Created progress indicators for long-running operations
- Designed a comprehensive argument structure with grouped options
- Provided clear help text and examples

Next Steps:
- Implement the OutputManager class
- Integrate with module interfaces from architecture design
- Implement argument parsing with argparse
- Connect with error handling system from algorithm design
- Create progress tracking callbacks for modules