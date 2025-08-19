/**
 * Consolidated File Upload Service
 * Handles all file upload operations with consistent error handling and progress tracking
 */

import { FileValidationService } from './FileValidationService';

export interface IFileUploadConfig {
  url: string;
  method?: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  timeout?: number;
  maxRetries?: number;
  chunkSize?: number;
  onProgress?: (progress: number) => void;
  onChunkComplete?: (chunkIndex: number, totalChunks: number) => void;
}

export interface IFileUploadResult {
  success: boolean;
  fileId?: string;
  fileUrl?: string;
  fileName?: string;
  fileSize?: number;
  message?: string;
  error?: string;
  metadata?: {
    uploadTime: number;
    serverResponse: any;
  };
}

export interface IFileUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed: number; // bytes per second
  estimatedTime: number; // seconds
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'cancelled';
}

export interface IBulkUploadResult {
  success: boolean;
  results: IFileUploadResult[];
  summary: {
    totalFiles: number;
    successfulUploads: number;
    failedUploads: number;
    totalSize: number;
    totalTime: number;
  };
}

export class FileUploadService {
  private static instance: FileUploadService;
  private uploadQueue: Map<string, AbortController> = new Map();
  private defaultConfig: IFileUploadConfig = {
    url: '/api/upload',
    method: 'POST',
    timeout: 30000, // 30 seconds
    maxRetries: 3,
    chunkSize: 1024 * 1024, // 1MB chunks
  };

  private constructor() {}

  /**
   * Get singleton instance
   */
  static getInstance(): FileUploadService {
    if (!FileUploadService.instance) {
      FileUploadService.instance = new FileUploadService();
    }
    return FileUploadService.instance;
  }

  /**
   * Upload a single file
   */
  async uploadFile(
    file: File,
    config: Partial<IFileUploadConfig> = {},
    additionalData?: Record<string, any>
  ): Promise<IFileUploadResult> {
    const uploadConfig = { ...this.defaultConfig, ...config };
    const uploadId = this.generateUploadId();

    try {
      // Validate file before upload
      const validation = new FileValidationService().validateFile(file);
      if (!validation.isValid) {
        return {
          success: false,
          error: `File validation failed: ${validation.errors.join(', ')}`,
          fileName: file.name,
          fileSize: file.size
        };
      }

      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Add additional data
      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, value);
        });
      }

      // Add metadata
      formData.append('metadata', JSON.stringify({
        originalName: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        uploadId
      }));

      // Perform upload
      const result = await this.performUpload(formData, uploadConfig, uploadId);
      
      return {
        ...result,
        fileName: file.name,
        fileSize: file.size
      };

    } catch (error) {
      console.error('File upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed',
        fileName: file.name,
        fileSize: file.size
      };
    } finally {
      this.uploadQueue.delete(uploadId);
    }
  }

  /**
   * Upload multiple files
   */
  async uploadFiles(
    files: File[],
    config: Partial<IFileUploadConfig> = {},
    additionalData?: Record<string, any>
  ): Promise<IBulkUploadResult> {
    const startTime = Date.now();
    const results: IFileUploadResult[] = [];
    let totalSize = 0;

    // Validate all files first
    const validation = new FileValidationService().validateFiles(files);
    if (!validation.isValid) {
      return {
        success: false,
        results: [],
        summary: {
          totalFiles: files.length,
          successfulUploads: 0,
          failedUploads: files.length,
          totalSize: 0,
          totalTime: Date.now() - startTime
        }
      };
    }

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      totalSize += file.size;

      // Update progress callback if provided
      if (config.onProgress) {
        config.onProgress((i / files.length) * 100);
      }

      const result = await this.uploadFile(file, config, additionalData);
      results.push(result);

      // Small delay between uploads to prevent server overload
      if (i < files.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    const successfulUploads = results.filter(r => r.success).length;
    const totalTime = Date.now() - startTime;

    return {
      success: successfulUploads === files.length,
      results,
      summary: {
        totalFiles: files.length,
        successfulUploads,
        failedUploads: files.length - successfulUploads,
        totalSize,
        totalTime
      }
    };
  }

  /**
   * Upload file in chunks for large files
   */
  async uploadFileInChunks(
    file: File,
    config: Partial<IFileUploadConfig> = {},
    additionalData?: Record<string, any>
  ): Promise<IFileUploadResult> {
    const uploadConfig = { ...this.defaultConfig, ...config };
    const chunkSize = uploadConfig.chunkSize || 1024 * 1024; // 1MB default
    const totalChunks = Math.ceil(file.size / chunkSize);
    const uploadId = this.generateUploadId();

    try {
      // Validate file
      const validation = new FileValidationService().validateFile(file);
      if (!validation.isValid) {
        return {
          success: false,
          error: `File validation failed: ${validation.errors.join(', ')}`,
          fileName: file.name,
          fileSize: file.size
        };
      }

      // Initialize upload on server
      const initResult = await this.initializeChunkedUpload(file, uploadConfig, uploadId);
      if (!initResult.success) {
        return initResult;
      }

      // Upload chunks
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);

        const chunkResult = await this.uploadChunk(
          chunk,
          chunkIndex,
          totalChunks,
          uploadId,
          uploadConfig,
          additionalData
        );

        if (!chunkResult.success) {
          return chunkResult;
        }

        // Update progress
        if (uploadConfig.onChunkComplete) {
          uploadConfig.onChunkComplete(chunkIndex + 1, totalChunks);
        }
        if (uploadConfig.onProgress) {
          uploadConfig.onProgress(((chunkIndex + 1) / totalChunks) * 100);
        }
      }

      // Finalize upload
      const finalizeResult = await this.finalizeChunkedUpload(uploadId, uploadConfig);
      
      return {
        ...finalizeResult,
        fileName: file.name,
        fileSize: file.size
      };

    } catch (error) {
      console.error('Chunked upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Chunked upload failed',
        fileName: file.name,
        fileSize: file.size
      };
    } finally {
      this.uploadQueue.delete(uploadId);
    }
  }

  /**
   * Cancel an ongoing upload
   */
  cancelUpload(uploadId: string): boolean {
    const controller = this.uploadQueue.get(uploadId);
    if (controller) {
      controller.abort();
      this.uploadQueue.delete(uploadId);
      return true;
    }
    return false;
  }

  /**
   * Cancel all ongoing uploads
   */
  cancelAllUploads(): void {
    this.uploadQueue.forEach(controller => controller.abort());
    this.uploadQueue.clear();
  }

  /**
   * Get upload progress for a specific upload
   */
  getUploadProgress(_uploadId: string): IFileUploadProgress | null {
    // This would need to be implemented with actual progress tracking
    // For now, return null as this is a basic implementation
    return null;
  }

  // === PRIVATE METHODS ===

  /**
   * Perform the actual upload
   */
  private async performUpload(
    formData: FormData,
    config: IFileUploadConfig,
    uploadId: string
  ): Promise<IFileUploadResult> {
    const controller = new AbortController();
    this.uploadQueue.set(uploadId, controller);

    const startTime = Date.now();

    try {
      const response = await fetch(config.url, {
        method: config.method,
        headers: config.headers,
        body: formData,
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const uploadTime = Date.now() - startTime;

      return {
        success: true,
        fileId: result.fileId || result.id,
        fileUrl: result.fileUrl || result.url,
        message: result.message || 'File uploaded successfully',
        metadata: {
          uploadTime,
          serverResponse: result
        }
      };

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          success: false,
          error: 'Upload cancelled'
        };
      }
      throw error;
    }
  }

  /**
   * Initialize chunked upload on server
   */
  private async initializeChunkedUpload(
    file: File,
    config: IFileUploadConfig,
    uploadId: string
  ): Promise<IFileUploadResult> {
    try {
      const response = await fetch(`${config.url}/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...config.headers
        },
        body: JSON.stringify({
          fileName: file.name,
          fileSize: file.size,
          fileType: file.type,
          uploadId,
          totalChunks: Math.ceil(file.size / (config.chunkSize || 1024 * 1024))
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize chunked upload: ${response.statusText}`);
      }

      await response.json(); // Response not used in this implementation
      return {
        success: true,
        fileId: uploadId,
        message: 'Chunked upload initialized'
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to initialize chunked upload'
      };
    }
  }

  /**
   * Upload a single chunk
   */
  private async uploadChunk(
    chunk: Blob,
    chunkIndex: number,
    totalChunks: number,
    uploadId: string,
    config: IFileUploadConfig,
    additionalData?: Record<string, any>
  ): Promise<IFileUploadResult> {
    try {
      const formData = new FormData();
      formData.append('chunk', chunk);
      formData.append('chunkIndex', chunkIndex.toString());
      formData.append('totalChunks', totalChunks.toString());
      formData.append('uploadId', uploadId);

      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, value);
        });
      }

      const response = await fetch(`${config.url}/chunk`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Failed to upload chunk ${chunkIndex}: ${response.statusText}`);
      }

      await response.json(); // Response not used in this implementation
      return {
        success: true,
        message: `Chunk ${chunkIndex + 1}/${totalChunks} uploaded successfully`
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : `Failed to upload chunk ${chunkIndex}`
      };
    }
  }

  /**
   * Finalize chunked upload
   */
  private async finalizeChunkedUpload(
    uploadId: string,
    config: IFileUploadConfig
  ): Promise<IFileUploadResult> {
    try {
      const response = await fetch(`${config.url}/finalize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...config.headers
        },
        body: JSON.stringify({ uploadId })
      });

      if (!response.ok) {
        throw new Error(`Failed to finalize upload: ${response.statusText}`);
      }

      const result = await response.json();
      return {
        success: true,
        fileId: result.fileId || result.id,
        fileUrl: result.fileUrl || result.url,
        message: 'File upload completed successfully'
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to finalize upload'
      };
    }
  }

  /**
   * Generate unique upload ID
   */
  private generateUploadId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
