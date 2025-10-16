export interface IFileMetadata {
  original_name: string;
  size: number;
  mime_type: string;
  file_path?: string;
  download_url?: string;
  preview_url?: string;
}

export interface IFileUploadResponse {
  success: boolean;
  message?: string;
  error?: string;
  metadata?: IFileMetadata;
  file_path?: string;
  download_url?: string;
}

export interface IFileValidationResult {
  isValid: boolean;
  error?: string;
}

export class FileService {
  private maxFileSize: number;
  private allowedTypes: string[];
  private baseUrl: string;

  constructor(maxFileSize: number = 10 * 1024 * 1024, baseUrl: string = '') { // Default 10MB
    this.maxFileSize = maxFileSize;
    this.baseUrl = baseUrl;
    this.allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/jpg',
      'image/png'
    ];
  }

  /**
   * Set the base URL for file operations
   */
  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): IFileValidationResult {
    // Check file type
    if (!this.allowedTypes.includes(file.type)) {
      return {
        isValid: false,
        error: 'File type not allowed. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG files only.'
      };
    }

    // Check file size
    if (file.size > this.maxFileSize) {
      return {
        isValid: false,
        error: `File size too large. Maximum allowed size is ${(this.maxFileSize / 1024 / 1024).toFixed(0)}MB.`
      };
    }

    return { isValid: true };
  }

  /**
   * Upload file to server
   */
  async uploadFile(
    file: File, 
    fileType: string = 'document', 
    description?: string,
    uploadUrl: string = '/api/upload'
  ): Promise<IFileUploadResponse> {
    try {
      // Validate file first
      const validation = this.validateFile(file);
      if (!validation.isValid) {
        return {
          success: false,
          error: validation.error
        };
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', fileType);
      if (description) {
        formData.append('description', description);
      }

      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('File upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed'
      };
    }
  }

  /**
   * Get file download URL
   */
  getFileDownloadUrl(fileData: string | File | { download_url?: string } | null | undefined): string | undefined {
    try {
      if (typeof fileData === "string") {
        // Check if it's Base64 data
        if (this.isBase64Data(fileData)) {
          return this.createBlobUrl(fileData);
        } else {
          // Handle file paths - construct full download URL
          // If it's already a full URL, return as is
          if (fileData.startsWith('http://') || fileData.startsWith('https://')) {
            return fileData;
          } else if (fileData.startsWith('/')) {
            // If it starts with /, it's a relative path that needs base URL
            if (this.baseUrl) {
              return `${this.baseUrl}${fileData}`;
            }
            return fileData;
          } else {
            // It's a file path that needs the API endpoint
            if (this.baseUrl) {
              return `${this.baseUrl}/api/files/download/${fileData}/`;
            } else {
              // Fallback to old behavior for backward compatibility
              return `/comperative_schedule/api/files/download/${fileData}`;
            }
          }
        }
      } else if (fileData && typeof fileData === 'object' && 'download_url' in fileData) {
        // Handle metadata objects with download_url
        return fileData.download_url;
      } else if (fileData instanceof File) {
        // Handle File objects - create temporary URL
        return URL.createObjectURL(fileData);
      }
      return undefined;
    } catch (err) {
      console.log("Error getting file URL: ", err);
      return undefined;
    }
  }

  /**
   * Check if data is Base64 encoded
   */
  private isBase64Data(data: string): boolean {
    return (
      data.startsWith('JVBERi0x') || // PDF Base64 header
      data.startsWith('UEsDBBQ') || // DOCX Base64 header
      data.startsWith('/9j/') ||     // JPEG Base64 header
      (data.length > 100 && /^[A-Za-z0-9+/=]+$/.test(data)) // Generic Base64 pattern
    );
  }

  /**
   * Create blob URL from Base64 data
   */
  private createBlobUrl(base64Data: string): string {
    try {
      const decodedData = atob(base64Data);
      const uint8Array = new Uint8Array(decodedData.length);
      for (let i = 0; i < decodedData.length; i++) {
        uint8Array[i] = decodedData.charCodeAt(i);
      }

      // Detect MIME type from Base64 header
      let mimeType = 'application/octet-stream';
      if (base64Data.startsWith('JVBERi0x')) {
        mimeType = 'application/pdf';
      } else if (base64Data.startsWith('UEsDBBQ')) {
        mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      } else if (base64Data.startsWith('/9j/')) {
        mimeType = 'image/jpeg';
      }

      const blob = new Blob([uint8Array], { type: mimeType });
      return URL.createObjectURL(blob);
    } catch (error) {
      console.error("Error creating blob URL:", error);
      throw new Error("Failed to process file data");
    }
  }

  /**
   * Generate filename for downloads
   */
  getDownloadFilename(fileData: string | File | null | undefined, defaultName: string = 'document'): string {
    if (!fileData || typeof fileData !== 'string') {
      return `${defaultName}.pdf`;
    }

    // Detect file type from Base64 header and return appropriate filename
    if (fileData.startsWith('JVBERi0x')) {
      return `${defaultName}.pdf`;
    } else if (fileData.startsWith('UEsDBBQ')) {
      return `${defaultName}.docx`;
    } else if (fileData.startsWith('/9j/')) {
      return `${defaultName}.jpg`;
    } else {
      return `${defaultName}.pdf`;
    }
  }

  /**
   * Download file
   */
  downloadFile(url: string, filename: string): void {
    try {
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // For blob URLs, don't set target="_blank" to force download
      if (!url.startsWith('blob:')) {
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
      }
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error downloading file:", error);
      throw new Error("Failed to download file");
    }
  }

  /**
   * Clean up blob URLs to prevent memory leaks
   */
  revokeBlobUrl(url: string): void {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url);
    }
  }

  /**
   * Get file size in human readable format
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file extension from filename
   */
  getFileExtension(filename: string): string {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
  }

  /**
   * Check if file is an image
   */
  isImageFile(file: File): boolean {
    return file.type.startsWith('image/');
  }

  /**
   * Check if file is a document
   */
  isDocumentFile(file: File): boolean {
    return file.type.includes('pdf') || file.type.includes('word') || file.type.includes('document');
  }

  /**
   * Create file preview (for images)
   */
  createFilePreview(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.isImageFile(file)) {
        reject(new Error('File is not an image'));
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          resolve(e.target.result as string);
        } else {
          reject(new Error('Failed to read file'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  }

  /**
   * Compress image file
   */
  async compressImage(file: File, maxWidth: number = 800, quality: number = 0.8): Promise<File> {
    return new Promise((resolve, reject) => {
      if (!this.isImageFile(file)) {
        reject(new Error('File is not an image'));
        return;
      }

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img;
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }

        canvas.width = width;
        canvas.height = height;

        // Draw and compress
        ctx?.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const compressedFile = new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now(),
              });
              resolve(compressedFile);
            } else {
              reject(new Error('Failed to compress image'));
            }
          },
          file.type,
          quality
        );
      };

      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = URL.createObjectURL(file);
    });
  }
}
