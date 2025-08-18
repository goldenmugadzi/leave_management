import { IBid } from "../types/scheduleTypes";
import { getApiEndpoints, buildApiUrl } from "../config/apiEndpoints";

export interface IBidData {
  cs_id: string;
  bid_count?: number;
  supplier?: string;
  supplier_name?: string;
  bid_date?: string;
  bid_document?: File | string;
  items: Array<{
    id?: number;
    item_required: string;
    unit_of_measurement: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    vat: string;
    ordered?: boolean;
  }>;
}

export interface IBidResponse {
  success: boolean;
  message?: string;
  error?: string;
  bid_id?: number;
}

export interface IBidCalculationResult {
  totalPrice: number;
  totalVAT: number;
  grandTotal: number;
  itemCount: number;
  isValid: boolean;
  errors: string[];
}

export interface IBidItemCalculation {
  item_required: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  vat: string;
  unit_of_measurement: string;
}

export class BidService {
  private baseUrl: string;
  private csrfToken: string;

  // Constants for bid validation
  private static readonly MIN_QUANTITY = 0.01;
  private static readonly MIN_UNIT_PRICE = 0.01;
  private static readonly MAX_QUANTITY = 999999;
  private static readonly MAX_UNIT_PRICE = 999999;
  private static readonly REQUIRED_FIELDS = ['quantity', 'unit_price', 'unit_of_measurement', 'vat'];

  constructor(baseUrl: string, csrfToken: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken;
  }

  // === BID CALCULATION METHODS ===

  /**
   * Calculate total price for a single item
   */
  calculateItemTotal(quantity: number, unitPrice: number): number {
    const qty = Number(quantity) || 0;
    const price = Number(unitPrice) || 0;
    return qty * price;
  }

  /**
   * Calculate VAT amount for an item
   */
  calculateVATAmount(totalPrice: number, vatRate: string): number {
    const total = Number(totalPrice) || 0;
    const vat = parseFloat(vatRate) || 0;
    return (total * vat) / 100;
  }

  /**
   * Calculate comprehensive bid totals including VAT
   */
  calculateBidTotals(items: IBidData['items']): IBidCalculationResult {
    if (!items || items.length === 0) {
      return {
        totalPrice: 0,
        totalVAT: 0,
        grandTotal: 0,
        itemCount: 0,
        isValid: true,
        errors: []
      };
    }

    let totalPrice = 0;
    let totalVAT = 0;
    const errors: string[] = [];

    items.forEach((item) => {
      const quantity = Number(item.quantity) || 0;
      const unitPrice = Number(item.unit_price) || 0;
      const itemTotal = this.calculateItemTotal(quantity, unitPrice);
      
      totalPrice += itemTotal;
      
      // Calculate VAT
      const vatAmount = this.calculateVATAmount(itemTotal, item.vat);
      totalVAT += vatAmount;

      // Validate item calculations
      if (itemTotal !== Number(item.total_price)) {
        errors.push(`Item "${item.item_required}": Calculated total (${itemTotal.toFixed(2)}) doesn't match stored total (${item.total_price})`);
      }
    });

    const grandTotal = totalPrice + totalVAT;

    return {
      totalPrice: Number(totalPrice.toFixed(2)),
      totalVAT: Number(totalVAT.toFixed(2)),
      grandTotal: Number(grandTotal.toFixed(2)),
      itemCount: items.length,
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Calculate bid total (legacy method for backward compatibility)
   */
  calculateBidTotal(items: IBidData['items']): number {
    const result = this.calculateBidTotals(items);
    return result.totalPrice;
  }

  /**
   * Recalculate all item totals in a bid
   */
  recalculateBidItems(bidData: IBidData): IBidData {
    if (!bidData.items || bidData.items.length === 0) {
      return bidData;
    }

    const updatedItems = bidData.items.map(item => ({
      ...item,
      total_price: this.calculateItemTotal(item.quantity, item.unit_price)
    }));

    return {
      ...bidData,
      items: updatedItems
    };
  }

  /**
   * Validate and recalculate a single bid item
   */
  validateAndRecalculateItem(
    item: IBidItemCalculation,
    fieldName: keyof IBidItemCalculation,
    newValue: string | number
  ): { updatedItem: IBidItemCalculation; isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const updatedItem = { ...item };

    // Update the field
    if (fieldName === 'quantity' || fieldName === 'unit_price') {
      const numValue = Number(newValue) || 0;
      (updatedItem as any)[fieldName] = numValue;
      
      // Validate range
      if (fieldName === 'quantity') {
        if (numValue < BidService.MIN_QUANTITY) {
          errors.push(`Quantity must be at least ${BidService.MIN_QUANTITY}`);
        }
        if (numValue > BidService.MAX_QUANTITY) {
          errors.push(`Quantity cannot exceed ${BidService.MAX_QUANTITY.toLocaleString()}`);
        }
      } else if (fieldName === 'unit_price') {
        if (numValue < BidService.MIN_UNIT_PRICE) {
          errors.push(`Unit price must be at least ${BidService.MIN_UNIT_PRICE}`);
        }
        if (numValue > BidService.MAX_UNIT_PRICE) {
          errors.push(`Unit price cannot exceed ${BidService.MAX_UNIT_PRICE.toLocaleString()}`);
        }
      }

      // Recalculate total price
      updatedItem.total_price = this.calculateItemTotal(
        updatedItem.quantity,
        updatedItem.unit_price
      );
    } else {
      (updatedItem as any)[fieldName] = newValue;
    }

    // Validate required fields
    BidService.REQUIRED_FIELDS.forEach(field => {
      const fieldValue = (updatedItem as any)[field];
      if (!fieldValue || String(fieldValue).trim() === '') {
        errors.push(`${field.replace('_', ' ').toUpperCase()} is required for item "${updatedItem.item_required}"`);
      }
    });

    return {
      updatedItem,
      isValid: errors.length === 0,
      errors
    };
  }

  // === BID VALIDATION METHODS ===

  /**
   * Comprehensive bid validation
   */
  validateBid(bidData: IBidData): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Basic bid validation
    if (!bidData.supplier_name?.trim()) {
      errors.push("Supplier name is required");
    }

    if (!bidData.bid_date) {
      errors.push("Bid date is required");
    }

    if (!bidData.bid_document) {
      errors.push("Bid document is required");
    }

    // Item validation
    if (!bidData.items || bidData.items.length === 0) {
      errors.push("At least one item is required");
    } else {
      bidData.items.forEach((item) => {
        if (!item.quantity || item.quantity <= 0) {
          errors.push(`Item "${item.item_required}": Quantity must be greater than 0`);
        }
        if (!item.unit_price || item.unit_price <= 0) {
          errors.push(`Item "${item.item_required}": Unit price must be greater than 0`);
        }
        if (!item.unit_of_measurement?.trim()) {
          errors.push(`Item "${item.item_required}": Unit of measurement is required`);
        }
        if (!item.vat?.trim()) {
          errors.push(`Item "${item.item_required}": VAT selection is required`);
        }

        // Validate calculations
        const expectedTotal = this.calculateItemTotal(item.quantity, item.unit_price);
        if (Math.abs(Number(item.total_price) - expectedTotal) > 0.01) {
          errors.push(`Item "${item.item_required}": Total price calculation mismatch (expected: ${expectedTotal.toFixed(2)}, actual: ${item.total_price})`);
        }
      });
    }

    // Business rule validation
    const calculationResult = this.calculateBidTotals(bidData.items);
    if (!calculationResult.isValid) {
      errors.push(...calculationResult.errors);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate bid items only
   */
  validateBidItems(items: IBidData['items']): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!items || items.length === 0) {
      errors.push("At least one item is required");
      return { isValid: false, errors };
    }

    items.forEach((item, index) => {
      // Required field validation
      if (!item.item_required?.trim()) {
        errors.push(`Item ${index + 1}: Item description is required`);
      }
      if (!item.quantity || item.quantity <= 0) {
        errors.push(`Item "${item.item_required}": Quantity must be greater than 0`);
      }
      if (!item.unit_price || item.unit_price <= 0) {
        errors.push(`Item "${item.item_required}": Unit price must be greater than 0`);
      }
      if (!item.unit_of_measurement?.trim()) {
        errors.push(`Item "${item.item_required}": Unit of measurement is required`);
      }
      if (!item.vat?.trim()) {
        errors.push(`Item "${item.item_required}": VAT selection is required`);
      }

      // Range validation
      if (item.quantity > BidService.MAX_QUANTITY) {
        errors.push(`Item "${item.item_required}": Quantity cannot exceed ${BidService.MAX_QUANTITY.toLocaleString()}`);
      }
      if (item.unit_price > BidService.MAX_UNIT_PRICE) {
        errors.push(`Item "${item.item_required}": Unit price cannot exceed ${BidService.MAX_UNIT_PRICE.toLocaleString()}`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // === BID BUSINESS LOGIC METHODS ===

  /**
   * Check if bid meets minimum requirements for submission
   */
  canSubmitBid(bidData: IBidData): { canSubmit: boolean; reasons: string[] } {
    const reasons: string[] = [];
    
    // Check if bid has items
    if (!bidData.items || bidData.items.length === 0) {
      reasons.push("Bid must contain at least one item");
    }

    // Check if all required fields are filled
    const validation = this.validateBid(bidData);
    if (!validation.isValid) {
      reasons.push(...validation.errors);
    }

    // Check if bid total is reasonable
    const totals = this.calculateBidTotals(bidData.items);
    if (totals.totalPrice <= 0) {
      reasons.push("Bid total must be greater than 0");
    }

    // Check if supplier is selected
    if (!bidData.supplier_name?.trim()) {
      reasons.push("Supplier must be selected");
    }

    return {
      canSubmit: reasons.length === 0,
      reasons
    };
  }

  /**
   * Get bid summary statistics
   */
  getBidSummary(bidData: IBidData): {
    itemCount: number;
    totalValue: number;
    averageItemValue: number;
    highestValueItem: string;
    lowestValueItem: string;
  } {
    if (!bidData.items || bidData.items.length === 0) {
      return {
        itemCount: 0,
        totalValue: 0,
        averageItemValue: 0,
        highestValueItem: '',
        lowestValueItem: ''
      };
    }

    const totals = this.calculateBidTotals(bidData.items);
    const averageValue = totals.itemCount > 0 ? totals.totalPrice / totals.itemCount : 0;

    let highestValue = 0;
    let lowestValue = Infinity;
    let highestItem = '';
    let lowestItem = '';

    bidData.items.forEach(item => {
      const itemTotal = Number(item.total_price) || 0;
      if (itemTotal > highestValue) {
        highestValue = itemTotal;
        highestItem = item.item_required;
      }
      if (itemTotal < lowestValue) {
        lowestValue = itemTotal;
        lowestItem = item.item_required;
      }
    });

    return {
      itemCount: totals.itemCount,
      totalValue: totals.totalPrice,
      averageItemValue: Number(averageValue.toFixed(2)),
      highestValueItem: highestItem,
      lowestValueItem: lowestItem
    };
  }

  // === API METHODS ===

  /**
   * Save a new bid
   */
  async saveBid(bidData: IBidData): Promise<IBidResponse> {
    try {
      // Validate bid before saving
      const validation = this.validateBid(bidData);
      if (!validation.isValid) {
        return {
          success: false,
          error: `Validation failed: ${validation.errors.join(', ')}`
        };
      }

      // Recalculate totals to ensure accuracy
      const recalculatedBid = this.recalculateBidItems(bidData);

      const formData = new FormData();
      formData.append("cs_id", recalculatedBid.cs_id);
      formData.append("bid_count", recalculatedBid.bid_count?.toString() || "");
      formData.append("supplier", recalculatedBid.supplier || "");
      formData.append("supplier_name", recalculatedBid.supplier_name || "");
      formData.append("bid_date", recalculatedBid.bid_date || "");
      
      // Handle bid document
      if (recalculatedBid.bid_document instanceof File) {
        formData.append("bid_document", recalculatedBid.bid_document);
      } else if (typeof recalculatedBid.bid_document === 'string') {
        formData.append("bid_document", recalculatedBid.bid_document);
      }
      
      formData.append("json_data", JSON.stringify({ items: recalculatedBid.items }));
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(`${this.baseUrl}/save_bid`, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving bid:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save bid"
      };
    }
  }

  /**
   * Update an existing bid
   */
  async updateBid(bidData: IBidData): Promise<IBidResponse> {
    try {
      if (!bidData.bid_count) {
        throw new Error("Bid count is required for updates");
      }

      return await this.saveBid(bidData);
    } catch (error) {
      console.error("Error updating bid:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update bid"
      };
    }
  }

  /**
   * Delete a bid
   */
  async deleteBid(csId: string, bidCount: number, supplierName: string): Promise<IBidResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("bid_count", JSON.stringify(bidCount));
      formData.append("supplier_name", supplierName);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(`${this.baseUrl}/delete_bid`, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error deleting bid:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete bid"
      };
    }
  }

  /**
   * Fetch bids for a comparative schedule
   */
  async fetchBids(csId: string): Promise<IBid[]> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_BIDS_DATA(csId)), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data && data.success && data.bids) {
        return data.bids;
      } else if (Array.isArray(data)) {
        return data;
      }
      
      return [];
    } catch (error) {
      console.error("Error fetching bids:", error);
      throw error;
    }
  }

  /**
   * Check if bid exists
   */
  async bidExists(csId: string, bidCount: number): Promise<boolean> {
    try {
      const bids = await this.fetchBids(csId);
      return bids.some(bid => bid.bid_count === bidCount);
    } catch (error) {
      console.error("Error checking if bid exists:", error);
      return false;
    }
  }

  /**
   * Get next bid count for a schedule
   */
  async getNextBidCount(csId: string): Promise<number> {
    try {
      const bids = await this.fetchBids(csId);
      if (bids.length === 0) return 1;
      
      const maxBidCount = Math.max(...bids.map(bid => bid.bid_count || 0));
      return maxBidCount + 1;
    } catch (error) {
      console.error("Error getting next bid count:", error);
      return 1;
    }
  }

  /**
   * Search suppliers
   */
  async searchSuppliers(searchQuery: string, limit: number = 100): Promise<any[]> {
    try {
      if (!searchQuery || searchQuery.length < 2) {
        return [];
      }

      const response = await fetch(buildApiUrl(this.baseUrl, `${getApiEndpoints().SUPPLIERS}?search=${encodeURIComponent(searchQuery)}&limit=${limit}`));
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.suppliers) {
        return data.suppliers;
      } else if (Array.isArray(data)) {
        return data;
      }
      
      return [];
    } catch (error) {
      console.error("Error searching suppliers:", error);
      return [];
    }
  }

  /**
   * Search UOM (Units of Measurement)
   */
  async searchUOM(searchQuery: string, limit: number = 100): Promise<any[]> {
    try {
      if (!searchQuery || searchQuery.length < 2) {
        return [];
      }

      const response = await fetch(buildApiUrl(this.baseUrl, `${getApiEndpoints().UOM}?search=${encodeURIComponent(searchQuery)}&limit=${limit}`));
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.uom) {
        return data.uom;
      } else if (Array.isArray(data)) {
        return data;
      }
      
      return [];
    } catch (error) {
      console.error("Error searching UOM:", error);
      return [];
    }
  }
}
