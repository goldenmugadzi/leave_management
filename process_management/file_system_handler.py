"""
Comprehensive file system error handling for knowledge center migration.

This module provides robust file system error handling including:
- File accessibility checks before creating database records
- Graceful handling of missing files with appropriate status marking
- File path sanitization for invalid characters
- Comprehensive error reporting and recovery
"""
import os
import re
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.files.storage import default_storage


class FileSystemErrorType(Enum):
    """Enumeration of file system error types."""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    INVALID_PATH = "invalid_path"
    CORRUPTED_FILE = "corrupted_file"
    DISK_FULL = "disk_full"
    NETWORK_ERROR = "network_error"
    ENCODING_ERROR = "encoding_error"
    PATH_TOO_LONG = "path_too_long"
    UNKNOWN_ERROR = "unknown_error"


class FileStatus(Enum):
    """Enumeration of file status values."""
    ACCESSIBLE = "accessible"
    MISSING = "missing"
    PERMISSION_DENIED = "permission_denied"
    CORRUPTED = "corrupted"
    INVALID_PATH = "invalid_path"
    INACCESSIBLE = "inaccessible"
    SANITIZED = "sanitized"


@dataclass
class FileSystemCheckResult:
    """Result of file system accessibility check."""
    file_path: str
    original_path: str
    status: FileStatus
    error_type: Optional[FileSystemErrorType] = None
    error_message: Optional[str] = None
    sanitized_path: Optional[str] = None
    file_size: Optional[int] = None
    last_modified: Optional[float] = None
    is_readable: bool = False
    is_writable: bool = False
    mime_type: Optional[str] = None
    encoding: Optional[str] = None


class FilePathSanitizer:
    """
    Sanitizes file paths to handle invalid characters and ensure compatibility.
    
    Provides comprehensive path sanitization including:
    - Invalid character removal/replacement
    - Unicode normalization
    - Path length validation
    - Reserved name handling
    """
    
    # Invalid characters for different operating systems
    INVALID_CHARS_WINDOWS = r'[<>:"/\\|?*\x00-\x1f]'
    INVALID_CHARS_UNIX = r'[\x00/]'
    
    # Reserved names on Windows
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    def __init__(self, max_path_length: int = 260, max_filename_length: int = 255):
        """
        Initialize path sanitizer.
        
        Args:
            max_path_length: Maximum allowed path length
            max_filename_length: Maximum allowed filename length
        """
        self.max_path_length = max_path_length
        self.max_filename_length = max_filename_length
        self.logger = logging.getLogger(__name__)
    
    def sanitize_path(self, file_path: str, replacement_char: str = '_') -> Tuple[str, List[str]]:
        """
        Sanitize a file path to ensure it's valid for the file system.
        
        Args:
            file_path: Original file path to sanitize
            replacement_char: Character to use for replacing invalid characters
            
        Returns:
            Tuple of (sanitized_path, list_of_changes_made)
        """
        changes = []
        original_path = file_path
        
        try:
            # Step 1: Unicode normalization
            normalized_path = unicodedata.normalize('NFKC', file_path)
            if normalized_path != file_path:
                changes.append(f"Unicode normalized: '{file_path}' -> '{normalized_path}'")
                file_path = normalized_path
            
            # Step 2: Split path into components
            path_obj = Path(file_path)
            directory = str(path_obj.parent) if path_obj.parent != Path('.') else ''
            filename = path_obj.name
            
            # Step 3: Sanitize directory path
            if directory:
                sanitized_directory, dir_changes = self._sanitize_directory_path(
                    directory, replacement_char
                )
                changes.extend(dir_changes)
            else:
                sanitized_directory = ''
            
            # Step 4: Sanitize filename
            sanitized_filename, file_changes = self._sanitize_filename(
                filename, replacement_char
            )
            changes.extend(file_changes)
            
            # Step 5: Reconstruct path
            if sanitized_directory:
                sanitized_path = os.path.join(sanitized_directory, sanitized_filename)
            else:
                sanitized_path = sanitized_filename
            
            # Step 6: Check path length
            if len(sanitized_path) > self.max_path_length:
                truncated_path = self._truncate_path(sanitized_path)
                changes.append(f"Path truncated due to length: '{sanitized_path}' -> '{truncated_path}'")
                sanitized_path = truncated_path
            
            # Step 7: Final validation
            if not self._is_valid_path(sanitized_path):
                # Fallback to a safe default
                safe_path = self._generate_safe_fallback_path(original_path)
                changes.append(f"Used fallback path due to validation failure: '{sanitized_path}' -> '{safe_path}'")
                sanitized_path = safe_path
            
        except Exception as e:
            self.logger.error(f"Error sanitizing path '{original_path}': {e}")
            # Generate a safe fallback
            sanitized_path = self._generate_safe_fallback_path(original_path)
            changes.append(f"Used fallback path due to sanitization error: '{original_path}' -> '{sanitized_path}'")
        
        return sanitized_path, changes
    
    def _sanitize_directory_path(self, directory: str, replacement_char: str) -> Tuple[str, List[str]]:
        """Sanitize directory path components."""
        changes = []
        
        # Split into path components
        components = directory.split(os.sep)
        sanitized_components = []
        
        for component in components:
            if not component:  # Skip empty components
                continue
                
            original_component = component
            
            # Remove invalid characters
            if os.name == 'nt':  # Windows
                component = re.sub(self.INVALID_CHARS_WINDOWS, replacement_char, component)
            else:  # Unix-like
                component = re.sub(self.INVALID_CHARS_UNIX, replacement_char, component)
            
            # Handle reserved names
            if component.upper() in self.RESERVED_NAMES:
                component = f"{component}_{replacement_char}"
                changes.append(f"Reserved name handled: '{original_component}' -> '{component}'")
            
            # Remove leading/trailing spaces and dots
            component = component.strip(' .')
            
            # Ensure component is not empty
            if not component:
                component = 'folder'
                changes.append(f"Empty component replaced: '{original_component}' -> '{component}'")
            
            if component != original_component:
                changes.append(f"Directory component sanitized: '{original_component}' -> '{component}'")
            
            sanitized_components.append(component)
        
        return os.sep.join(sanitized_components), changes
    
    def _sanitize_filename(self, filename: str, replacement_char: str) -> Tuple[str, List[str]]:
        """Sanitize filename."""
        changes = []
        original_filename = filename
        
        if not filename:
            return 'unnamed_file', [f"Empty filename replaced with 'unnamed_file'"]
        
        # Split filename and extension
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, extension = name_parts
        else:
            name, extension = filename, ''
        
        # Sanitize name part
        original_name = name
        
        # Remove invalid characters
        if os.name == 'nt':  # Windows
            name = re.sub(self.INVALID_CHARS_WINDOWS, replacement_char, name)
        else:  # Unix-like
            name = re.sub(self.INVALID_CHARS_UNIX, replacement_char, name)
        
        # Handle reserved names
        if name.upper() in self.RESERVED_NAMES:
            name = f"{name}_{replacement_char}"
            changes.append(f"Reserved filename handled: '{original_name}' -> '{name}'")
        
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        
        # Ensure name is not empty
        if not name:
            name = 'unnamed'
            changes.append(f"Empty filename replaced: '{original_name}' -> '{name}'")
        
        # Reconstruct filename
        if extension:
            sanitized_filename = f"{name}.{extension}"
        else:
            sanitized_filename = name
        
        # Check filename length
        if len(sanitized_filename) > self.max_filename_length:
            # Truncate name part while preserving extension
            max_name_length = self.max_filename_length - len(extension) - 1 if extension else self.max_filename_length
            truncated_name = name[:max_name_length]
            sanitized_filename = f"{truncated_name}.{extension}" if extension else truncated_name
            changes.append(f"Filename truncated: '{name}.{extension}' -> '{sanitized_filename}'")
        
        if sanitized_filename != original_filename:
            changes.append(f"Filename sanitized: '{original_filename}' -> '{sanitized_filename}'")
        
        return sanitized_filename, changes
    
    def _truncate_path(self, path: str) -> str:
        """Truncate path to fit within maximum length."""
        if len(path) <= self.max_path_length:
            return path
        
        path_obj = Path(path)
        directory = str(path_obj.parent)
        filename = path_obj.name
        
        # Calculate available space for directory
        available_space = self.max_path_length - len(filename) - 1  # -1 for separator
        
        if available_space > 0:
            truncated_directory = directory[:available_space]
            return os.path.join(truncated_directory, filename)
        else:
            # If even the filename is too long, truncate it
            max_filename_length = self.max_path_length
            return filename[:max_filename_length]
    
    def _is_valid_path(self, path: str) -> bool:
        """Validate that a path is acceptable."""
        try:
            # Basic checks
            if not path or len(path) > self.max_path_length:
                return False
            
            # Check for null bytes
            if '\x00' in path:
                return False
            
            # Platform-specific validation
            if os.name == 'nt':  # Windows
                if re.search(self.INVALID_CHARS_WINDOWS, path):
                    return False
            else:  # Unix-like
                if re.search(self.INVALID_CHARS_UNIX, path):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _generate_safe_fallback_path(self, original_path: str) -> str:
        """Generate a safe fallback path when sanitization fails."""
        import hashlib
        import time
        
        # Create a hash of the original path
        path_hash = hashlib.md5(original_path.encode('utf-8', errors='ignore')).hexdigest()[:8]
        timestamp = str(int(time.time()))
        
        return f"sanitized_file_{timestamp}_{path_hash}"


class FileSystemAccessibilityChecker:
    """
    Checks file system accessibility and provides detailed error information.
    
    Performs comprehensive checks including:
    - File existence verification
    - Permission checks (read/write)
    - File integrity validation
    - Path validation
    - File metadata extraction
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize accessibility checker.
        
        Args:
            base_path: Base path for relative file paths
        """
        self.base_path = base_path or getattr(settings, 'MEDIA_ROOT', '')
        self.path_sanitizer = FilePathSanitizer()
        self.logger = logging.getLogger(__name__)
    
    def check_file_accessibility(self, file_path: str, 
                               perform_sanitization: bool = True) -> FileSystemCheckResult:
        """
        Perform comprehensive file accessibility check.
        
        Args:
            file_path: Path to the file to check
            perform_sanitization: Whether to attempt path sanitization
            
        Returns:
            FileSystemCheckResult with detailed information
        """
        original_path = file_path
        
        try:
            # Step 1: Path sanitization if requested
            sanitized_path = None
            if perform_sanitization:
                sanitized_path, changes = self.path_sanitizer.sanitize_path(file_path)
                if changes:
                    self.logger.info(f"Path sanitized: {file_path} -> {sanitized_path}")
                    file_path = sanitized_path
            
            # Step 2: Resolve full path
            if not os.path.isabs(file_path):
                full_path = os.path.join(self.base_path, file_path)
            else:
                full_path = file_path
            
            # Step 3: Basic existence check
            if not os.path.exists(full_path):
                return FileSystemCheckResult(
                    file_path=file_path,
                    original_path=original_path,
                    status=FileStatus.MISSING,
                    error_type=FileSystemErrorType.FILE_NOT_FOUND,
                    error_message=f"File not found: {full_path}",
                    sanitized_path=sanitized_path
                )
            
            # Step 4: Check if it's actually a file (not a directory)
            if not os.path.isfile(full_path):
                return FileSystemCheckResult(
                    file_path=file_path,
                    original_path=original_path,
                    status=FileStatus.INVALID_PATH,
                    error_type=FileSystemErrorType.INVALID_PATH,
                    error_message=f"Path is not a file: {full_path}",
                    sanitized_path=sanitized_path
                )
            
            # Step 5: Permission checks
            is_readable = os.access(full_path, os.R_OK)
            is_writable = os.access(full_path, os.W_OK)
            
            if not is_readable:
                return FileSystemCheckResult(
                    file_path=file_path,
                    original_path=original_path,
                    status=FileStatus.PERMISSION_DENIED,
                    error_type=FileSystemErrorType.PERMISSION_DENIED,
                    error_message=f"Permission denied reading file: {full_path}",
                    sanitized_path=sanitized_path,
                    is_readable=is_readable,
                    is_writable=is_writable
                )
            
            # Step 6: Get file metadata
            try:
                stat_info = os.stat(full_path)
                file_size = stat_info.st_size
                last_modified = stat_info.st_mtime
            except OSError as e:
                return FileSystemCheckResult(
                    file_path=file_path,
                    original_path=original_path,
                    status=FileStatus.INACCESSIBLE,
                    error_type=FileSystemErrorType.PERMISSION_DENIED,
                    error_message=f"Cannot access file metadata: {e}",
                    sanitized_path=sanitized_path
                )
            
            # Step 7: Basic file integrity check
            try:
                with open(full_path, 'rb') as f:
                    # Try to read first few bytes to verify file is not corrupted
                    f.read(1024)
            except (IOError, OSError) as e:
                return FileSystemCheckResult(
                    file_path=file_path,
                    original_path=original_path,
                    status=FileStatus.CORRUPTED,
                    error_type=FileSystemErrorType.CORRUPTED_FILE,
                    error_message=f"File appears to be corrupted: {e}",
                    sanitized_path=sanitized_path,
                    file_size=file_size,
                    last_modified=last_modified,
                    is_readable=is_readable,
                    is_writable=is_writable
                )
            
            # Step 8: Detect MIME type and encoding (optional)
            mime_type = self._detect_mime_type(full_path)
            encoding = self._detect_encoding(full_path)
            
            # Step 9: Success case
            status = FileStatus.SANITIZED if sanitized_path != original_path else FileStatus.ACCESSIBLE
            
            return FileSystemCheckResult(
                file_path=file_path,
                original_path=original_path,
                status=status,
                sanitized_path=sanitized_path,
                file_size=file_size,
                last_modified=last_modified,
                is_readable=is_readable,
                is_writable=is_writable,
                mime_type=mime_type,
                encoding=encoding
            )
            
        except Exception as e:
            self.logger.error(f"Unexpected error checking file accessibility for '{file_path}': {e}")
            return FileSystemCheckResult(
                file_path=file_path,
                original_path=original_path,
                status=FileStatus.INACCESSIBLE,
                error_type=FileSystemErrorType.UNKNOWN_ERROR,
                error_message=f"Unexpected error: {e}",
                sanitized_path=sanitized_path
            )
    
    def _detect_mime_type(self, file_path: str) -> Optional[str]:
        """Detect MIME type of the file."""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type
        except Exception:
            return None
    
    def _detect_encoding(self, file_path: str) -> Optional[str]:
        """Detect encoding of text files."""
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # Read first 8KB
                result = chardet.detect(raw_data)
                return result.get('encoding') if result else None
        except Exception:
            return None
    
    def batch_check_files(self, file_paths: List[str], 
                         perform_sanitization: bool = True) -> List[FileSystemCheckResult]:
        """
        Perform batch file accessibility checks.
        
        Args:
            file_paths: List of file paths to check
            perform_sanitization: Whether to attempt path sanitization
            
        Returns:
            List of FileSystemCheckResult instances
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.check_file_accessibility(file_path, perform_sanitization)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error checking file '{file_path}': {e}")
                results.append(FileSystemCheckResult(
                    file_path=file_path,
                    original_path=file_path,
                    status=FileStatus.INACCESSIBLE,
                    error_type=FileSystemErrorType.UNKNOWN_ERROR,
                    error_message=f"Batch check error: {e}"
                ))
        
        return results


class FileSystemErrorHandler:
    """
    Handles file system errors with appropriate recovery strategies.
    
    Provides comprehensive error handling including:
    - Error categorization and logging
    - Recovery strategy application
    - Status marking for database records
    - Error reporting and statistics
    """
    
    def __init__(self):
        """Initialize file system error handler."""
        self.accessibility_checker = FileSystemAccessibilityChecker()
        self.error_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def handle_file_system_error(self, file_path: str, 
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle file system error with appropriate recovery strategy.
        
        Args:
            file_path: Path to the problematic file
            context: Additional context information
            
        Returns:
            Dictionary containing error handling results
        """
        context = context or {}
        
        # Perform accessibility check
        check_result = self.accessibility_checker.check_file_accessibility(file_path)
        
        # Create error record
        error_record = {
            'file_path': file_path,
            'original_path': check_result.original_path,
            'status': check_result.status.value,
            'error_type': check_result.error_type.value if check_result.error_type else None,
            'error_message': check_result.error_message,
            'sanitized_path': check_result.sanitized_path,
            'file_size': check_result.file_size,
            'is_readable': check_result.is_readable,
            'is_writable': check_result.is_writable,
            'mime_type': check_result.mime_type,
            'context': context,
            'timestamp': timezone.now().isoformat() if 'timezone' in globals() else None,
            'recovery_applied': False,
            'recovery_strategy': None
        }
        
        # Apply recovery strategy based on error type
        if check_result.error_type:
            recovery_result = self._apply_recovery_strategy(check_result, context)
            error_record.update(recovery_result)
        
        # Log the error
        self.error_log.append(error_record)
        self.logger.error(f"File system error for '{file_path}': {check_result.error_message}")
        
        return error_record
    
    def _apply_recovery_strategy(self, check_result: FileSystemCheckResult, 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply appropriate recovery strategy based on error type.
        
        Args:
            check_result: Result from accessibility check
            context: Additional context information
            
        Returns:
            Dictionary containing recovery results
        """
        recovery_result = {
            'recovery_applied': False,
            'recovery_strategy': None,
            'recovery_message': None,
            'suggested_action': None
        }
        
        if not check_result.error_type:
            return recovery_result
        
        error_type = check_result.error_type
        
        if error_type == FileSystemErrorType.FILE_NOT_FOUND:
            recovery_result.update({
                'recovery_strategy': 'mark_as_missing',
                'recovery_message': 'File marked as missing in database',
                'suggested_action': 'Create document record with missing status',
                'recovery_applied': True
            })
            
        elif error_type == FileSystemErrorType.PERMISSION_DENIED:
            recovery_result.update({
                'recovery_strategy': 'mark_as_inaccessible',
                'recovery_message': 'File marked as inaccessible due to permissions',
                'suggested_action': 'Create document record with permission error status',
                'recovery_applied': True
            })
            
        elif error_type == FileSystemErrorType.INVALID_PATH:
            if check_result.sanitized_path:
                recovery_result.update({
                    'recovery_strategy': 'use_sanitized_path',
                    'recovery_message': f'Using sanitized path: {check_result.sanitized_path}',
                    'suggested_action': 'Retry with sanitized path',
                    'recovery_applied': True
                })
            else:
                recovery_result.update({
                    'recovery_strategy': 'mark_as_invalid',
                    'recovery_message': 'Path cannot be sanitized, marking as invalid',
                    'suggested_action': 'Create document record with invalid path status',
                    'recovery_applied': True
                })
                
        elif error_type == FileSystemErrorType.CORRUPTED_FILE:
            recovery_result.update({
                'recovery_strategy': 'mark_as_corrupted',
                'recovery_message': 'File marked as corrupted',
                'suggested_action': 'Create document record with corrupted status',
                'recovery_applied': True
            })
            
        elif error_type == FileSystemErrorType.PATH_TOO_LONG:
            recovery_result.update({
                'recovery_strategy': 'truncate_path',
                'recovery_message': 'Path truncated to fit system limits',
                'suggested_action': 'Use truncated path for database record',
                'recovery_applied': True
            })
            
        else:
            recovery_result.update({
                'recovery_strategy': 'mark_as_error',
                'recovery_message': f'Unknown error type: {error_type.value}',
                'suggested_action': 'Create document record with error status',
                'recovery_applied': True
            })
        
        return recovery_result
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive error summary.
        
        Returns:
            Dictionary containing error statistics and details
        """
        if not self.error_log:
            return {
                'total_errors': 0,
                'error_types': {},
                'status_distribution': {},
                'recovery_success_rate': 0.0,
                'recent_errors': []
            }
        
        # Count errors by type
        error_types = {}
        status_distribution = {}
        recovery_applied_count = 0
        
        for error in self.error_log:
            error_type = error.get('error_type', 'unknown')
            status = error.get('status', 'unknown')
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            if error.get('recovery_applied', False):
                recovery_applied_count += 1
        
        recovery_success_rate = (recovery_applied_count / len(self.error_log)) * 100
        
        return {
            'total_errors': len(self.error_log),
            'error_types': error_types,
            'status_distribution': status_distribution,
            'recovery_success_rate': recovery_success_rate,
            'recent_errors': self.error_log[-10:] if len(self.error_log) > 10 else self.error_log,
            'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def clear_error_log(self):
        """Clear the error log."""
        self.error_log.clear()