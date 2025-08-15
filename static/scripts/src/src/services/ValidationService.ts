export interface IValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface IScheduleValidationData {
  currency?: any;
  procPlan?: any;
  scope_of_work?: string;
  pr_number?: string;
  pr_date?: string;
  closing_date?: string;
  reference_date?: string;
  closing_time?: string;
  cs_opened_date?: string;
  tac_date?: string;
  advert?: File | any;
}

export interface IBidValidationData {
  supplier_name?: string;
  bid_date?: string;
  bid_document?: File | string;
  items?: Array<{
    quantity?: number;
    unit_price?: number;
    unit_of_measurement?: string;
    vat?: string;
  }>;
}

export interface IComplianceValidationData {
  cs_id?: string;
  compliance?: any[];
  complianceRemarks?: any[];
}

export class ValidationService {
  /**
   * Validate schedule data
   */
  validateSchedule(data: IScheduleValidationData): IValidationResult {
    const errors: string[] = [];

    if (!data.currency) {
      errors.push("Currency is required");
    }

    if (!data.procPlan) {
      errors.push("Procurement plan is required");
    }

    if (!data.scope_of_work?.trim()) {
      errors.push("Scope of work is required");
    }

    if (!data.pr_number?.trim()) {
      errors.push("PR number is required");
    }

    // Enhanced date validation
    if (!data.pr_date || data.pr_date.trim() === '') {
      errors.push("PR date is required");
    } else if (!this.isValidDateFormat(data.pr_date)) {
      errors.push("PR date must be in YYYY-MM-DD format");
    }

    if (!data.closing_date || data.closing_date.trim() === '') {
      errors.push("Closing date is required");
    } else if (!this.isValidDateFormat(data.closing_date)) {
      errors.push("Closing date must be in YYYY-MM-DD format");
    }

    if (!data.reference_date || data.reference_date.trim() === '') {
      errors.push("Reference date is required");
    } else if (!this.isValidDateFormat(data.reference_date)) {
      errors.push("Reference date must be in YYYY-MM-DD format");
    }

    if (!data.closing_time?.trim()) {
      errors.push("Closing time is required");
    }

    if (!data.cs_opened_date || data.cs_opened_date.trim() === '') {
      errors.push("CS opened date is required");
    } else if (!this.isValidDateFormat(data.cs_opened_date)) {
      errors.push("CS opened date must be in YYYY-MM-DD format");
    }

    if (!data.tac_date || data.tac_date.trim() === '') {
      errors.push("TAC date is required");
    } else if (!this.isValidDateFormat(data.tac_date)) {
      errors.push("TAC date must be in YYYY-MM-DD format");
    }

    // Check for either new advert file or existing advert metadata
    if (!data.advert) {
      errors.push("Advertisement document is required");
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate date format (YYYY-MM-DD)
   */
  private isValidDateFormat(dateString: string): boolean {
    if (!dateString || typeof dateString !== 'string') return false;
    
    // Check if it matches YYYY-MM-DD format
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(dateString)) return false;
    
    // Check if it's a valid date
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return false;
    
    // Check if the parsed date matches the input string (prevents dates like 2024-13-45)
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    
    return formattedDate === dateString;
  }

  /**
   * Validate bid data
   */
  validateBid(data: IBidValidationData): IValidationResult {
    const errors: string[] = [];

    if (!data.supplier_name?.trim()) {
      errors.push("Supplier name is required");
    }

    if (!data.bid_date) {
      errors.push("Bid date is required");
    }

    if (!data.bid_document) {
      errors.push("Bid document is required");
    }

    if (!data.items || data.items.length === 0) {
      errors.push("At least one item is required");
    } else {
      data.items.forEach((item, index) => {
        if (!item.quantity || item.quantity <= 0) {
          errors.push(`Item ${index + 1}: Quantity must be greater than 0`);
        }
        if (!item.unit_price || item.unit_price <= 0) {
          errors.push(`Item ${index + 1}: Unit price must be greater than 0`);
        }
        if (!item.unit_of_measurement?.trim()) {
          errors.push(`Item ${index + 1}: Unit of measurement is required`);
        }
        if (!item.vat?.trim()) {
          errors.push(`Item ${index + 1}: VAT selection is required`);
        }
      });
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate compliance data
   */
  validateCompliance(data: IComplianceValidationData): IValidationResult {
    const errors: string[] = [];

    if (!data.cs_id) {
      errors.push("CS ID is required");
    }

    if (!data.compliance || data.compliance.length === 0) {
      errors.push("Compliance data is required");
    }

    if (!data.complianceRemarks || data.complianceRemarks.length === 0) {
      errors.push("Compliance remarks are required");
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate email format
   */
  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate phone number format
   */
  validatePhoneNumber(phone: string): boolean {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
  }

  /**
   * Validate date format
   */
  validateDate(date: string): boolean {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(date)) return false;
    
    const dateObj = new Date(date);
    return dateObj instanceof Date && !isNaN(dateObj.getTime());
  }

  /**
   * Validate date range
   */
  validateDateRange(startDate: string, endDate: string): IValidationResult {
    const errors: string[] = [];

    if (!this.validateDate(startDate)) {
      errors.push("Invalid start date format");
    }

    if (!this.validateDate(endDate)) {
      errors.push("Invalid end date format");
    }

    if (startDate && endDate && startDate > endDate) {
      errors.push("Start date cannot be after end date");
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate numeric value
   */
  validateNumeric(value: any, min?: number, max?: number): IValidationResult {
    const errors: string[] = [];

    if (value === null || value === undefined || value === '') {
      errors.push("Value is required");
      return { isValid: false, errors };
    }

    const numValue = Number(value);
    if (isNaN(numValue)) {
      errors.push("Value must be a valid number");
      return { isValid: false, errors };
    }

    if (min !== undefined && numValue < min) {
      errors.push(`Value must be at least ${min}`);
    }

    if (max !== undefined && numValue > max) {
      errors.push(`Value must be at most ${max}`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate required field
   */
  validateRequired(value: any, fieldName: string): IValidationResult {
    const errors: string[] = [];

    if (value === null || value === undefined || value === '') {
      errors.push(`${fieldName} is required`);
    } else if (typeof value === 'string' && value.trim() === '') {
      errors.push(`${fieldName} cannot be empty`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate string length
   */
  validateStringLength(value: string, fieldName: string, minLength?: number, maxLength?: number): IValidationResult {
    const errors: string[] = [];

    if (minLength !== undefined && value.length < minLength) {
      errors.push(`${fieldName} must be at least ${minLength} characters long`);
    }

    if (maxLength !== undefined && value.length > maxLength) {
      errors.push(`${fieldName} must be no more than ${maxLength} characters long`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate file
   */
  validateFile(file: File, allowedTypes?: string[], maxSize?: number): IValidationResult {
    const errors: string[] = [];

    if (!file) {
      errors.push("File is required");
      return { isValid: false, errors };
    }

    if (allowedTypes && !allowedTypes.includes(file.type)) {
      errors.push(`File type not allowed. Allowed types: ${allowedTypes.join(', ')}`);
    }

    if (maxSize && file.size > maxSize) {
      const maxSizeMB = (maxSize / 1024 / 1024).toFixed(2);
      errors.push(`File size too large. Maximum allowed size is ${maxSizeMB}MB`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate business rules
   */
  validateBusinessRules(data: any, rules: Array<{
    condition: (data: any) => boolean;
    message: string;
  }>): IValidationResult {
    const errors: string[] = [];

    rules.forEach(rule => {
      if (!rule.condition(data)) {
        errors.push(rule.message);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate form data with multiple validators
   */
  validateFormData(data: any, validators: Array<{
    field: string;
    validators: Array<(value: any) => IValidationResult>;
  }>): IValidationResult {
    const errors: string[] = [];

    validators.forEach(({ field, validators }) => {
      const value = data[field];
      validators.forEach(validator => {
        const result = validator(value);
        if (!result.isValid) {
          errors.push(...result.errors);
        }
      });
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Sanitize input string
   */
  sanitizeString(input: string): string {
    return input
      .trim()
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/&/g, '&amp;') // Escape HTML entities
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  /**
   * Format validation errors for display
   */
  formatValidationErrors(errors: string[]): string {
    if (errors.length === 0) return '';
    
    if (errors.length === 1) {
      return errors[0];
    }
    
    return errors.map((error, index) => `${index + 1}. ${error}`).join('\n');
  }
}
