/**
 * Consolidated File Validation Service
 * Standardizes file validation across all services and components
 */

export interface IFileValidationConfig {
  allowedTypes: string[];
  maxSize: number;
  maxFiles?: number;
  allowedExtensions?: string[];
  validateContent?: boolean;
}

export interface IFileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
  metadata?: {
    size: number;
    type: string;
    extension: string;
    name: string;
  };
}

export interface IFileUploadResult {
  success: boolean;
  file?: File;
  errors: string[];
  warnings?: string[];
}

export class FileValidationService {
  // Default configurations for different file types
  private static readonly DEFAULT_CONFIGS = {
    document: {
      allowedTypes: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/csv'
      ],
      allowedExtensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'],
      maxSize: 10 * 1024 * 1024, // 10MB
      validateContent: false
    },
    image: {
      allowedTypes: [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp'
      ],
      allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
      maxSize: 5 * 1024 * 1024, // 5MB
      validateContent: true
    },
    archive: {
      allowedTypes: [
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/gzip'
      ],
      allowedExtensions: ['.zip', '.rar', '.7z', '.gz', '.tar'],
      maxSize: 50 * 1024 * 1024, // 50MB
      validateContent: false
    },
    general: {
      allowedTypes: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'application/zip',
        'application/x-rar-compressed',
        'text/plain',
        'text/csv'
      ],
      allowedExtensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.zip', '.rar', '.txt', '.csv'],
      maxSize: 20 * 1024 * 1024, // 20MB
      validateContent: false
    }
  };

  /**
   * Validate a single file against configuration
   */
  validateFile(file: File, config: IFileValidationConfig | string = 'general'): IFileValidationResult {
    const validationConfig = typeof config === 'string' 
      ? FileValidationService.DEFAULT_CONFIGS[config as keyof typeof FileValidationService.DEFAULT_CONFIGS] || FileValidationService.DEFAULT_CONFIGS.general
      : config;

    const errors: string[] = [];
    const warnings: string[] = [];
    const metadata = {
      size: file.size,
      type: file.type,
      extension: this.getFileExtension(file.name),
      name: file.name
    };

    // Check if file exists
    if (!file) {
      errors.push('No file provided');
      return { isValid: false, errors, metadata };
    }

    // Size validation
    if (file.size > validationConfig.maxSize) {
      const maxSizeMB = (validationConfig.maxSize / 1024 / 1024).toFixed(1);
      errors.push(`File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum allowed size of ${maxSizeMB}MB`);
    }

    // File type validation
    if (validationConfig.allowedTypes && validationConfig.allowedTypes.length > 0) {
      if (!validationConfig.allowedTypes.includes(file.type)) {
        errors.push(`File type '${file.type}' is not allowed. Allowed types: ${validationConfig.allowedTypes.join(', ')}`);
      }
    }

    // Extension validation
    if (validationConfig.allowedExtensions && validationConfig.allowedExtensions.length > 0) {
      const fileExtension = this.getFileExtension(file.name);
      if (!validationConfig.allowedExtensions.includes(fileExtension)) {
        errors.push(`File extension '${fileExtension}' is not allowed. Allowed extensions: ${validationConfig.allowedExtensions.join(', ')}`);
      }
    }

    // Content validation (basic)
    if (validationConfig.validateContent) {
      const contentValidation = this.validateFileContent(file);
      if (!contentValidation.isValid) {
        errors.push(...contentValidation.errors);
      }
    }

    // Security checks
    const securityChecks = this.performSecurityChecks(file);
    if (!securityChecks.isValid) {
      errors.push(...securityChecks.errors);
    }

    // Warning for large files
    if (file.size > validationConfig.maxSize * 0.8) {
      warnings.push('File size is approaching the maximum limit');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      metadata
    };
  }

  /**
   * Validate multiple files
   */
  validateFiles(files: File[], config: IFileValidationConfig | string = 'general', maxFiles?: number): IFileValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    let totalSize = 0;

    // Check file count
    if (maxFiles && files.length > maxFiles) {
      errors.push(`Maximum ${maxFiles} files allowed. Received ${files.length} files.`);
    }

    // Validate each file
    files.forEach((file, index) => {
      const fileValidation = this.validateFile(file, config);
      if (!fileValidation.isValid) {
        errors.push(`File ${index + 1} (${file.name}): ${fileValidation.errors.join(', ')}`);
      }
      if (fileValidation.warnings) {
        warnings.push(`File ${index + 1} (${file.name}): ${fileValidation.warnings.join(', ')}`);
      }
      totalSize += file.size;
    });

    // Check total size
    const validationConfig = typeof config === 'string' 
      ? FileValidationService.DEFAULT_CONFIGS[config as keyof typeof FileValidationService.DEFAULT_CONFIGS] || FileValidationService.DEFAULT_CONFIGS.general
      : config;
    
    if (totalSize > validationConfig.maxSize * 2) {
      warnings.push('Total file size is significantly large and may impact performance');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate file content (basic implementation)
   */
  private validateFileContent(file: File): IFileValidationResult {
    const errors: string[] = [];

    // Check for empty files
    if (file.size === 0) {
      errors.push('File is empty');
    }

    // Check for suspicious file names
    if (this.isSuspiciousFileName(file.name)) {
      errors.push('File name contains suspicious characters');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Perform security checks on file
   */
  private performSecurityChecks(file: File): IFileValidationResult {
    const errors: string[] = [];

    // Check for double extensions (potential security risk)
    if (file.name.includes('..')) {
      errors.push('File name contains suspicious double dots');
    }

    // Check for executable files
    const executableExtensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js'];
    const fileExtension = this.getFileExtension(file.name).toLowerCase();
    if (executableExtensions.includes(fileExtension)) {
      errors.push('Executable files are not allowed for security reasons');
    }

    // Check file name length
    if (file.name.length > 255) {
      errors.push('File name is too long');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get file extension from filename
   */
  private getFileExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) return '';
    return filename.substring(lastDotIndex).toLowerCase();
  }

  /**
   * Check if filename is suspicious
   */
  private isSuspiciousFileName(filename: string): boolean {
    const suspiciousPatterns = [
      /\.\./, // Double dots
      /[<>:"|?*]/, // Invalid characters
      /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i, // Reserved names
      /^\./, // Hidden files
      /\.$/, // Ends with dot
    ];

    return suspiciousPatterns.some(pattern => pattern.test(filename));
  }

  /**
   * Get human-readable file size
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file type category
   */
  static getFileCategory(file: File): string {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    if (file.type.includes('pdf') || file.type.includes('document') || file.type.includes('text')) return 'document';
    if (file.type.includes('spreadsheet') || file.type.includes('excel')) return 'spreadsheet';
    if (file.type.includes('presentation') || file.type.includes('powerpoint')) return 'presentation';
    if (file.type.includes('zip') || file.type.includes('rar') || file.type.includes('compressed')) return 'archive';
    return 'other';
  }

  /**
   * Check if file is an image
   */
  static isImage(file: File): boolean {
    return file.type.startsWith('image/');
  }

  /**
   * Check if file is a document
   */
  static isDocument(file: File): boolean {
    return file.type.includes('pdf') || 
           file.type.includes('document') || 
           file.type.includes('text') ||
           file.type.includes('spreadsheet') ||
           file.type.includes('presentation');
  }

  /**
   * Check if file is an archive
   */
  static isArchive(file: File): boolean {
    return file.type.includes('zip') || 
           file.type.includes('rar') || 
           file.type.includes('compressed') ||
           file.type.includes('tar') ||
           file.type.includes('7z');
  }

  /**
   * Get recommended configuration for file type
   */
  static getRecommendedConfig(file: File): IFileValidationConfig {
    if (FileValidationService.isImage(file)) {
      return FileValidationService.DEFAULT_CONFIGS.image;
    } else if (FileValidationService.isDocument(file)) {
      return FileValidationService.DEFAULT_CONFIGS.document;
    } else if (FileValidationService.isArchive(file)) {
      return FileValidationService.DEFAULT_CONFIGS.archive;
    } else {
      return FileValidationService.DEFAULT_CONFIGS.general;
    }
  }
}
