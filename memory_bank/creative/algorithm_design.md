# 🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM DESIGN 🎨🎨🎨

Focus: Error handling and recovery mechanisms for Website SEO Orchestrator
Objective: Design robust error handling patterns that provide clear error reporting, graceful recovery, and maintainable code
Requirements:
- Support comprehensive error tracking across modules
- Provide meaningful error messages for troubleshooting
- Enable graceful recovery from non-critical failures
- Support dry-run simulation without actual system changes
- Implement proper cleanup on failure

## Context

### System Requirements
- Detailed logging and error handling throughout the application
- Ability to recover from certain types of failures
- Support for dry-run capability to simulate operations
- State management between module executions
- Comprehensive reporting of failures

### Technical Constraints
- Must work with Python 3.11+ exception handling mechanisms
- Must integrate with structured logging system
- Must support both synchronous and potentially asynchronous operations
- Must maintain backward compatibility with existing module error patterns

## Problem Analysis

### Error Types and Categories
- **Configuration Errors**: Issues with configuration files, parameters, or environment variables
- **Authentication Errors**: Problems with credentials or access rights
- **Network Errors**: Connection issues, timeouts, or API failures
- **Data Processing Errors**: Problems with content parsing, generation, or transformation
- **File System Errors**: Issues with reading, writing, or manipulating files
- **External Service Errors**: Failures in external dependencies (Node.js, Hostinger API)
- **State Management Errors**: Issues with workflow state or context data

### Recovery Scenarios
- **Retryable Operations**: Network timeouts, temporary service unavailability
- **Partial Success Scenarios**: Some operations completed successfully, others failed
- **Rollback Opportunities**: Situations where previous state can be restored
- **Continue Despite Errors**: Non-critical failures that shouldn't halt the entire process
- **Fatal Errors**: Situations requiring immediate termination

## Algorithm Options

### Option 1: Hierarchical Exception Classes with Metadata

#### Description
Create a hierarchical exception class structure with rich metadata about the error context, enabling precise error handling and recovery strategies based on exception type and attributes.

#### Pseudocode
```python
class OrchestratorError(Exception):
    """Base class for all orchestrator errors."""
    def __init__(self, message, module=None, operation=None, recoverable=False, context=None):
        self.message = message
        self.module = module
        self.operation = operation
        self.recoverable = recoverable
        self.context = context or {}
        super().__init__(f"{module or 'Orchestrator'} error during {operation}: {message}")

# Specific error types inherit from base
class ConfigurationError(OrchestratorError):
    """Error related to configuration issues."""
    pass

class NetworkError(OrchestratorError):
    """Error related to network operations."""
    def __init__(self, *args, retryable=True, **kwargs):
        self.retryable = retryable
        super().__init__(*args, recoverable=retryable, **kwargs)

# Error handling strategy
def execute_with_recovery(module, operation, context, max_retries=3):
    retries = 0
    while True:
        try:
            return module.execute(operation, context)
        except NetworkError as e:
            if e.retryable and retries < max_retries:
                retries += 1
                # Log retry attempt
                continue
            # Log failure and re-raise
            raise
        except OrchestratorError as e:
            if e.recoverable:
                # Log recovery attempt
                # Apply recovery strategy
                continue
            # Log failure and re-raise
            raise
```

#### Pros
- Comprehensive error classification
- Rich metadata for error handling decisions
- Clear hierarchical structure
- Strong type checking capabilities
- Good separation of error types

#### Cons
- More complex exception hierarchy to maintain
- Requires consistent use across all modules
- More verbose exception creation
- May lead to excessive class proliferation
- Overhead in passing context information

#### Technical Fit: High
#### Complexity: Medium
#### Scalability: High

### Option 2: Result Objects with Error States

#### Description
Instead of using exceptions, return result objects that contain success/failure status, data, and error information, allowing for more complex success/failure scenarios and easier error propagation.

#### Pseudocode
```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

class ResultStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"

@dataclass
class Result:
    status: ResultStatus
    data: Optional[Dict[str, Any]] = None
    errors: Optional[Dict[str, Any]] = None
    
    @property
    def is_success(self):
        return self.status == ResultStatus.SUCCESS
    
    @property
    def is_partial(self):
        return self.status == ResultStatus.PARTIAL
    
    @property
    def is_failure(self):
        return self.status == ResultStatus.FAILURE
    
    @classmethod
    def success(cls, data=None):
        return cls(ResultStatus.SUCCESS, data=data)
    
    @classmethod
    def failure(cls, error_message, module=None, operation=None, context=None):
        errors = {
            "message": error_message,
            "module": module,
            "operation": operation,
            "context": context or {}
        }
        return cls(ResultStatus.FAILURE, errors=errors)
    
    @classmethod
    def partial(cls, data=None, errors=None):
        return cls(ResultStatus.PARTIAL, data=data, errors=errors)

# Usage example
def process_website(website_name):
    result = exporter.export(website_name)
    if result.is_failure:
        return result  # Propagate error
    
    if result.is_partial:
        # Log warning about partial success
        pass
    
    export_data = result.data
    content_result = generator.generate(website_name, export_data)
    # Additional logic...
```

#### Pros
- Handles complex success/failure scenarios
- Avoids exception handling overhead
- Clear and explicit error propagation
- Good for partial success scenarios
- Easy to extend with additional metadata

#### Cons
- More verbose than exception-based approach
- Requires checking result status everywhere
- May lead to deeply nested success/failure checks
- Different from conventional Python error handling
- Potential for silent error propagation

#### Technical Fit: Medium
#### Complexity: Medium
#### Scalability: High

### Option 3: Context Manager with Rollback

#### Description
Use context managers to define atomic operations with automatic cleanup and rollback capabilities, ensuring resources are properly managed even during failures.

#### Pseudocode
```python
import contextlib
import logging

logger = logging.getLogger("orchestrator")

class ModuleOperation:
    def __init__(self, module, operation, context, cleanup_func=None):
        self.module = module
        self.operation = operation
        self.context = context
        self.cleanup_func = cleanup_func
        self.result = None
        self.started = False
        
    def __enter__(self):
        logger.info(f"Starting {self.operation} in {self.module}")
        self.started = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error during {self.operation} in {self.module}: {exc_val}")
            if self.cleanup_func:
                try:
                    logger.info(f"Attempting cleanup for {self.operation}")
                    self.cleanup_func(self.context)
                    logger.info(f"Cleanup successful for {self.operation}")
                except Exception as e:
                    logger.error(f"Cleanup failed for {self.operation}: {e}")
        return False  # Don't suppress the exception

# Usage example
def process_website(website_name):
    context = {"website_name": website_name}
    
    try:
        with ModuleOperation("exporter", "export", context, cleanup_func=cleanup_export):
            export_result = exporter.export(website_name)
            context["export_data"] = export_result
        
        with ModuleOperation("generator", "generate", context, cleanup_func=cleanup_generation):
            content_result = generator.generate(context)
            context["content_data"] = content_result
            
        # Additional operations...
    except Exception as e:
        logger.error(f"Process failed for {website_name}: {e}")
        return False
        
    return True
```

#### Pros
- Clean resource management
- Automatic cleanup on failure
- Clear operation boundaries
- Follows Python's context manager pattern
- Good for managing stateful operations

#### Cons
- More complex to implement
- May not handle partial success well
- Less flexible for recovery strategies
- Nested context managers can be hard to read
- May not fit all operation types

#### Technical Fit: Medium
#### Complexity: High
#### Scalability: Medium

### Option 4: Decorator-Based Error Handling

#### Description
Use decorators to apply consistent error handling, retry logic, and logging across module methods, reducing boilerplate and ensuring uniform error handling.

#### Pseudocode
```python
import functools
import logging
import time
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger("orchestrator")

def handle_errors(
    retries: int = 0,
    retry_delay: float = 1.0,
    recoverable_exceptions: tuple = (TimeoutError, ConnectionError),
    log_level: int = logging.ERROR
):
    """Decorator for consistent error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            max_attempts = retries + 1
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except recoverable_exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Recoverable error in {func.__name__}, "
                            f"retrying {attempt}/{retries}: {e}"
                        )
                        time.sleep(retry_delay)
                    else:
                        logger.log(
                            log_level, 
                            f"Maximum retries reached for {func.__name__}: {e}"
                        )
                except Exception as e:
                    logger.log(
                        log_level, 
                        f"Error in {func.__name__}: {e}"
                    )
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator

# Usage example
class ExporterModule:
    @handle_errors(retries=3, retry_delay=2.0)
    def export(self, website_name):
        # Implementation...
        return export_data
```

#### Pros
- Reduces boilerplate code
- Ensures consistent error handling
- Easy to apply across many functions
- Centralized error handling logic
- Good separation of concerns

#### Cons
- May hide complexity
- Less flexible for complex recovery scenarios
- May be harder to debug
- Can't easily maintain state between retries
- May not fit all error handling needs

#### Technical Fit: High
#### Complexity: Low
#### Scalability: Medium

## Decision

### Chosen Option: Hybrid Approach - Hierarchical Exceptions with Decorators

#### Rationale
A hybrid approach combining hierarchical exception classes with decorator-based error handling provides the best balance of flexibility, consistency, and maintainability. This approach leverages Python's native exception handling while adding structure through a well-defined hierarchy, and it ensures consistent handling through decorators for common patterns like retries.

This addresses the key requirements:
- **Comprehensive Error Tracking**: Rich metadata in exceptions for detailed tracking
- **Meaningful Error Messages**: Structured error information for clear reporting
- **Graceful Recovery**: Decorators for retry logic and recovery strategies
- **Dry-Run Support**: Exception metadata can include dry-run context
- **Proper Cleanup**: Decorators can ensure cleanup happens consistently

### Implementation Considerations

#### Exception Hierarchy Design
```python
class OrchestratorError(Exception):
    """Base class for all orchestrator errors."""
    def __init__(self, message, module=None, operation=None, recoverable=False, context=None):
        self.message = message
        self.module = module
        self.operation = operation
        self.recoverable = recoverable
        self.context = context or {}
        super().__init__(self._format_message(message, module, operation))
    
    def _format_message(self, message, module, operation):
        parts = []
        if module:
            parts.append(f"[{module}]")
        if operation:
            parts.append(f"during {operation}:")
        parts.append(message)
        return " ".join(parts)

# Configuration errors
class ConfigurationError(OrchestratorError):
    """Error related to configuration issues."""
    pass

# Authentication errors
class AuthenticationError(OrchestratorError):
    """Error related to authentication issues."""
    pass

# Network errors
class NetworkError(OrchestratorError):
    """Error related to network operations."""
    def __init__(self, *args, retryable=True, **kwargs):
        self.retryable = retryable
        super().__init__(*args, recoverable=retryable, **kwargs)

# Data processing errors
class DataError(OrchestratorError):
    """Error related to data processing."""
    pass

# File system errors
class FileSystemError(OrchestratorError):
    """Error related to file system operations."""
    pass

# External service errors
class ExternalServiceError(OrchestratorError):
    """Error related to external service calls."""
    def __init__(self, *args, service=None, retryable=True, **kwargs):
        self.service = service
        self.retryable = retryable
        kwargs["module"] = kwargs.get("module", service)
        super().__init__(*args, recoverable=retryable, **kwargs)

# State management errors
class StateError(OrchestratorError):
    """Error related to state management."""
    pass
```

#### Decorator Implementation
```python
import functools
import logging
import time
from typing import Callable, Any, Dict, Optional, Tuple, Type, Union

logger = logging.getLogger("orchestrator")

def with_error_handling(
    retries: int = 0,
    retry_delay: float = 1.0,
    retry_backoff: float = 1.0,
    recoverable_exceptions: Tuple[Type[Exception], ...] = (NetworkError, ExternalServiceError),
    capture_context: bool = True,
    log_level: int = logging.ERROR,
    cleanup_func: Optional[Callable] = None
):
    """Decorator for consistent error handling with retries and cleanup."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            module_name = kwargs.get("module_name", func.__module__)
            operation = func.__name__
            context = {}
            
            # Capture context if enabled
            if capture_context:
                context.update({
                    "args": args,
                    "kwargs": {k: v for k, v in kwargs.items() if not k.startswith("_")},
                    "function": func.__name__,
                    "module": module_name
                })
            
            # Handle dry run mode
            dry_run = kwargs.get("dry_run", False)
            if dry_run:
                logger.info(f"DRY RUN: Would execute {operation} in {module_name}")
                context["dry_run"] = True
            
            attempt = 0
            max_attempts = retries + 1
            current_delay = retry_delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except recoverable_exceptions as e:
                    attempt += 1
                    
                    # Check if the exception is actually retryable
                    retryable = getattr(e, "retryable", True)
                    if not retryable:
                        logger.log(log_level, f"Non-retryable error in {operation}: {e}")
                        raise
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Recoverable error in {operation}, "
                            f"retrying {attempt}/{retries} in {current_delay:.1f}s: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= retry_backoff  # Exponential backoff
                    else:
                        logger.log(
                            log_level, 
                            f"Maximum retries reached for {operation}: {e}"
                        )
                        raise
                except OrchestratorError as e:
                    # Enhance error with context if not already present
                    if capture_context and not hasattr(e, "context"):
                        e.context = context
                    logger.log(log_level, f"Orchestrator error in {operation}: {e}")
                    
                    # Call cleanup if provided
                    if cleanup_func:
                        try:
                            cleanup_func(*args, **kwargs)
                        except Exception as cleanup_error:
                            logger.error(f"Cleanup error after {operation} failed: {cleanup_error}")
                    
                    raise
                except Exception as e:
                    # Wrap unknown exceptions in OrchestratorError
                    wrapped = OrchestratorError(
                        str(e), 
                        module=module_name,
                        operation=operation,
                        context=context
                    )
                    logger.log(log_level, f"Unexpected error in {operation}: {e}")
                    
                    # Call cleanup if provided
                    if cleanup_func:
                        try:
                            cleanup_func(*args, **kwargs)
                        except Exception as cleanup_error:
                            logger.error(f"Cleanup error after {operation} failed: {cleanup_error}")
                    
                    raise wrapped from e
        
        return wrapper
    
    return decorator
```

#### Error Logging Enhancement
```python
def configure_error_logging(logger):
    """Configure enhanced error logging for orchestrator errors."""
    def error_formatter(record):
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if issubclass(exc_type, OrchestratorError):
                # Add detailed context from the exception
                record.context = getattr(exc_value, "context", {})
                record.module = getattr(exc_value, "module", "unknown")
                record.operation = getattr(exc_value, "operation", "unknown")
                record.recoverable = getattr(exc_value, "recoverable", False)
        return record
    
    # Add filter to enhance log records
    logger.addFilter(error_formatter)
    
    # Configure handler with custom formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(module)s - %(operation)s - %(message)s"
    )
    
    # Apply formatter to handlers
    for handler in logger.handlers:
        handler.setFormatter(formatter)
```

#### Centralized Error Handler
```python
def handle_module_error(e, website_name, step, dry_run=False):
    """Centralized error handler for module errors."""
    logger = logging.getLogger("orchestrator.error_handler")
    
    if dry_run:
        logger.info(f"DRY RUN: Would handle error in {step} for {website_name}: {e}")
        return True
    
    # Log detailed error information
    logger.error(f"Error during {step} for {website_name}: {e}")
    
    # Check if error is recoverable
    if isinstance(e, OrchestratorError) and e.recoverable:
        logger.info(f"Attempting recovery for {website_name} after {step} error")
        # Apply recovery strategy based on error type
        try:
            if isinstance(e, NetworkError):
                # Network recovery logic
                pass
            elif isinstance(e, ExternalServiceError):
                # External service recovery logic
                pass
            else:
                # Generic recovery logic
                pass
            
            logger.info(f"Recovery successful for {website_name} after {step} error")
            return True
        except Exception as recovery_error:
            logger.error(f"Recovery failed for {website_name}: {recovery_error}")
            return False
    
    return False  # Non-recoverable error
```

## Validation

### Requirements Met
- [✓] Support comprehensive error tracking across modules
- [✓] Provide meaningful error messages for troubleshooting
- [✓] Enable graceful recovery from non-critical failures
- [✓] Support dry-run simulation without actual system changes
- [✓] Implement proper cleanup on failure

### Technical Feasibility
The proposed error handling approach is technically feasible and aligns well with Python's exception handling model while adding structured metadata and consistent behaviors through decorators. The implementation can be adapted to both synchronous and asynchronous code with minimal changes.

### Risk Assessment
- **Complexity**: Medium risk - requires consistent application across modules
- **Learning Curve**: Low risk - follows Python's exception patterns with enhancements
- **Performance Impact**: Low risk - minimal overhead from exception handling
- **Integration**: Medium risk - requires updating existing error handling approaches

🎨 CREATIVE CHECKPOINT: Error Handling Pattern
- Progress: Complete
- Decisions: Hybrid approach with hierarchical exceptions and decorators
- Next steps: Integrate with logging system and module interfaces

## Usage Patterns

### Basic Error Handling
```python
@with_error_handling(retries=3)
def export_website(website_name, config, workspace):
    """Export website content."""
    try:
        # Implementation...
        return export_data
    except requests.ConnectionError as e:
        raise NetworkError(
            f"Failed to connect to Hostinger: {e}",
            module="exporter",
            operation="export_website",
            retryable=True
        )
    except requests.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            raise AuthenticationError(
                "Invalid Hostinger credentials",
                module="exporter",
                operation="export_website",
                recoverable=False
            )
        # Handle other HTTP errors...
```

### Recovery Strategy
```python
def run_pipeline(config, website_name, steps, dry_run=False):
    """Run the specified pipeline steps."""
    context = {
        "website_name": website_name,
        "config": config,
        "dry_run": dry_run
    }
    
    for step in steps:
        try:
            if step == "export":
                export_website(context)
            elif step == "generate":
                generate_content(context)
            # Additional steps...
        except OrchestratorError as e:
            # Try to recover
            if handle_module_error(e, website_name, step, dry_run):
                continue  # Continue to next step if recovery was successful
            else:
                # Log error and exit
                return False
    
    return True
```

### Dry Run Implementation
```python
@with_error_handling()
def export_website(context):
    """Export website content."""
    website_name = context["website_name"]
    config = context["config"]
    dry_run = context.get("dry_run", False)
    
    logger = logging.getLogger("orchestrator.exporter")
    
    if dry_run:
        logger.info(f"DRY RUN: Would export website {website_name}")
        # Simulate result data
        return {"files": [], "export_time": "2023-04-01T12:00:00"}
    
    # Actual implementation...
```

# 🎨🎨🎨 EXITING CREATIVE PHASE 🎨🎨🎨

Summary: Designed a comprehensive error handling system using a hybrid approach of hierarchical exception classes and decorator-based error handling to provide rich error context, consistent recovery patterns, and clean integration with logging.

Key Decisions:
- Adopted hierarchical exception classes with rich metadata
- Implemented decorator-based error handling for retry logic and cleanup
- Created centralized error handler for recovery strategies
- Integrated dry-run support throughout error handling
- Enhanced logging system for detailed error reporting

Next Steps:
- Implement base exception classes and error handling decorators
- Integrate with module interfaces defined in architecture design
- Create specific exception subclasses for different error categories
- Develop recovery strategies for common failure scenarios
- Update logging configuration to support enhanced error reporting 