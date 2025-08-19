/**
 * File utility functions
 * Centralized location for file handling helpers used across the application
 */

/**
 * Generate filename for Base64 downloads based on file content
 * @param fileData - File data (Base64 string, File object, or null)
 * @param defaultName - Default filename without extension
 * @returns Generated filename with appropriate extension
 */
export const getDownloadFilename = (
  fileData: string | File | null | undefined, 
  defaultName: string = 'document'
): string => {
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
};

/**
 * Validate file type and size
 * @param file - File object to validate
 * @param allowedTypes - Array of allowed MIME types
 * @param maxSize - Maximum file size in bytes
 * @returns Validation result with success status and error message
 */
export const validateFile = (
  file: File, 
  allowedTypes: string[] = [
    'application/pdf',
    'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/jpg', 
    'image/png'
  ],
  maxSize: number = 10 * 1024 * 1024 // 10MB
): { isValid: boolean; error?: string } => {
  // Check file type
  if (!allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: 'File type not allowed. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG files only.'
    };
  }

  // Check file size
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `File size too large. Maximum allowed size is ${(maxSize / 1024 / 1024).toFixed(0)}MB.`
    };
  }

  return { isValid: true };
};

/**
 * Get file extension from filename
 * @param filename - Filename to extract extension from
 * @returns File extension without dot (e.g., 'pdf', 'docx')
 */
export const getFileExtension = (filename: string): string => {
  return filename.split('.').pop()?.toLowerCase() || '';
};

/**
 * Check if file extension is allowed
 * @param filename - Filename to check
 * @param allowedExtensions - Array of allowed extensions
 * @returns True if file extension is allowed
 */
export const isAllowedFileExtension = (
  filename: string, 
  allowedExtensions: string[] = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
): boolean => {
  const extension = getFileExtension(filename);
  return allowedExtensions.includes(extension);
};
