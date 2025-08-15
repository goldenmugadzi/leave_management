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

export class BidService {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string, csrfToken: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken;
  }

  /**
   * Save a new bid
   */
  async saveBid(bidData: IBidData): Promise<IBidResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", bidData.cs_id);
      formData.append("bid_count", bidData.bid_count?.toString() || "");
      formData.append("supplier", bidData.supplier || "");
      formData.append("supplier_name", bidData.supplier_name || "");
      formData.append("bid_date", bidData.bid_date || "");
      
      // Handle bid document
      if (bidData.bid_document instanceof File) {
        formData.append("bid_document", bidData.bid_document);
      } else if (typeof bidData.bid_document === 'string') {
        formData.append("bid_document", bidData.bid_document);
      }
      
      formData.append("json_data", JSON.stringify({ items: bidData.items }));
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
   * Validate bid data
   */
  validateBid(bidData: IBidData): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!bidData.supplier_name?.trim()) {
      errors.push("Supplier name is required");
    }

    if (!bidData.bid_date) {
      errors.push("Bid date is required");
    }

    if (!bidData.bid_document && !bidData.bid_document) {
      errors.push("Bid document is required");
    }

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
      });
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Calculate bid total
   */
  calculateBidTotal(items: IBidData['items']): number {
    if (!items || items.length === 0) return 0;
    
    return items.reduce((sum, item) => {
      const itemTotal = Number(item.total_price) || 0;
      return sum + itemTotal;
    }, 0);
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
