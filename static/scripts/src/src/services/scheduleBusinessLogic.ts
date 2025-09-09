import { useScheduleStore } from '../stores/scheduleStore';
import ScheduleApiService, { ApiResponse } from './scheduleApiService';
import { IBid } from '../types/scheduleTypes';

export class ScheduleBusinessLogic {
  private apiService: ScheduleApiService;
  private store: any; // Using any for now to avoid TypeScript issues

  constructor(baseUrl: string) {
    this.apiService = new ScheduleApiService(baseUrl);
    this.store = useScheduleStore.getState();
  }

  /**
   * Initialize the schedule - either load existing CS or prepare for new one
   */
  async initializeSchedule(csId?: string, prId?: string): Promise<ApiResponse<any>> {
    this.store.setIsLoading(true);
    this.store.setLoadingOperation("Initializing schedule");

    try {
      if (csId) {
        await this.loadExistingSchedule(csId);
      } else if (prId) {
        await this.loadPRData(prId);
      }
      
      // Load reference data
      await this.loadReferenceData();
      
      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.store.setResponse({
        open: true,
        title: "Error",
        message: `Failed to initialize schedule: ${errorMessage}`,
        success: false
      });
      
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      this.store.setIsLoading(false);
      this.store.setLoadingOperation("");
    }
  }

  /**
   * Load existing comparative schedule data
   */
  private async loadExistingSchedule(csId: string): Promise<void> {
    const response = await this.apiService.fetchCS(csId);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch CS data');
    }
    
    const data = response.data as any;
    
    // Update store with CS data
    this.store.initializeSchedule({
      csId: data.cs_id,
      csOwner: data.cs_owner,
      creator: data.creator,
      createdAt: data.created_at,
      storedPrId: data.pr_id?.toString() || '',
      procRef: data.proc_plan?.proc_ref || '',
      username: this.store.username,
    });

    // Set reference data if available
    if (data.users) this.store.setUsers(data.users as any);
    if (data.suppliers) this.store.setSuppliers(data.suppliers as any);
    if (data.proc_plans) this.store.setProcPlans(data.proc_plans as any);
    if (data.currencies) this.store.setCurrencies(data.currencies as any);
    if (data.currency) this.store.setCurrency(data.currency as any);
    if (data.proc_plan) {
      this.store.setProcPlan(data.proc_plan as any);
      this.store.setProcRef(data.proc_plan.proc_ref);
    }

    // Set PR data
    if (data.pr_number || data.scope_of_work) {
      this.store.setPrData({
        pr_number: data.pr_number || '',
        pr_date: data.pr_date || '',
        reference_date: data.ref_date || '',
        procurement_plan_description: data.proc_plan?.description || '',
        procurement_plan_id: data.proc_plan?.id?.toString() || '',
        currency: data.currency?.currency || '',
        closing_date: data.closing_date || '',
        closing_time: data.closing_time || '',
        cs_opened_date: data.cs_opened || '',
        scope_of_work: data.scope_of_work || '',
        tac_date: data.tac_date || '',
        region: data.region || '',
        show_site_visit: data.show_site_visit || false,
        show_samples_required: data.show_samples_required || false,
        internal_notes: data.additional_notes || '',
        items: []
      });
    }

    // Process items
    const allItems: Array<{
      id: string;
      name: string;
      quantity: number;
      unit: string;
      status: string;
      included: boolean;
    }> = [];

    if (data.cs_items && Array.isArray(data.cs_items)) {
      (data.cs_items as any[]).forEach((item: any) => {
        allItems.push({
          id: item.id?.toString() || '',
          name: item.item_required || '',
          quantity: item.quantity || 0,
          unit: item.unit_of_measurement || '',
          status: 'included_in_cs',
          included: true
        });
      });
    }

    if (data.pr_items && Array.isArray(data.pr_items)) {
      (data.pr_items as any[]).forEach((item: any) => {
        const existsInCS = allItems.some(csItem => csItem.id === item.id?.toString());
        if (!existsInCS) {
          allItems.push({
            id: item.id?.toString() || '',
            name: item.item_required || '',
            quantity: item.quantity || 0,
            unit: item.unit_of_measurement || '',
            status: item.ordered ? 'used_in_other_schedule' : 'available',
            included: false
          });
        }
      });
    }

    this.store.setPrData({ items: allItems });

    // Load other data
    if (data.bids && Array.isArray(data.bids)) {
      this.store.setBids(data.bids);
      this.store.setBidCount(data.bids.length);
    }

    if (data.committee && Array.isArray(data.committee)) {
      this.store.setCommitteeMembers(data.committee);
    }

    if (data.compliance && Array.isArray(data.compliance)) {
      this.store.setCompliance(data.compliance);
    }

    if (data.complianceRemarks && Array.isArray(data.complianceRemarks)) {
      this.store.setComplianceRemarks(data.complianceRemarks);
    }

    if (data.rankings && Array.isArray(data.rankings)) {
      this.store.setRankings(data.rankings);
    }

    // Handle advertisement metadata
    if (data.advert) {
      this.handleAdvertisementData(data.advert);
    }
  }

  /**
   * Load PR data for new schedule
   */
  private async loadPRData(prId: string): Promise<void> {
    const prResponse = await this.apiService.fetchPR(prId);
    
    if (!prResponse.success || !prResponse.data) {
      throw new Error(prResponse.error || 'Failed to fetch PR data');
    }
    
    const prData = prResponse.data;
    
    this.store.setPrData({
      pr_number: prData.pr_id || '',
      pr_date: prData.pr_date || '',
      reference_date: prData.pr_date || '',
      procurement_plan_description: prData.proc_plan?.description || '',
      procurement_plan_id: prData.proc_plan?.id?.toString() || '',
      scope_of_work: prData.scope_of_work || '',
      items: []
    });

    if (prData.proc_plan) {
      this.store.setProcPlan(prData.proc_plan);
      this.store.setProcRef(prData.proc_plan.proc_ref);
    }

    // Load PR items
    const itemsResponse = await this.apiService.fetchPRItems(prId, 1, 50);
    if (itemsResponse.success && itemsResponse.data?.pr_items) {
      const items = itemsResponse.data.pr_items.map((item: any) => ({
        id: item.id.toString(),
        name: item.item_required,
        quantity: item.quantity,
        unit: item.unit_of_measurement,
        status: item.ordered ? 'used_in_other_schedule' : 'available',
        included: !item.ordered
      }));
      
      this.store.setPrData({ items });
    }
  }

  /**
   * Load reference data
   */
  private async loadReferenceData(): Promise<void> {
    const refResponse = await this.apiService.fetchReferenceData();
    
    if (refResponse.success && refResponse.data) {
      if (refResponse.data.suppliers) this.store.setSuppliers(refResponse.data.suppliers);
      if (refResponse.data.users) this.store.setUsers(refResponse.data.users);
      if (refResponse.data.currencies) this.store.setCurrencies(refResponse.data.currencies);
      if (refResponse.data.proc_plans) this.store.setProcPlans(refResponse.data.proc_plans);
    }
  }

  /**
   * Handle advertisement data
   */
  private handleAdvertisementData(advertData: string): void {
    const isBase64 = (
      advertData.startsWith('JVBERi0x') || 
      advertData.startsWith('UEsDBBQ') || 
      advertData.startsWith('/9j/') ||     
      (advertData.length > 100 && /^[A-Za-z0-9+/=]+$/.test(advertData))
    );

    if (isBase64) {
      try {
        const decodedData = atob(advertData);
        const uint8Array = new Uint8Array(decodedData.length);
        for (let i = 0; i < decodedData.length; i++) {
          uint8Array[i] = decodedData.charCodeAt(i);
        }

        let mimeType = 'application/pdf';
        let extension = '.pdf';
        if (advertData.startsWith('JVBERi0x')) {
          mimeType = 'application/pdf';
          extension = '.pdf';
        } else if (advertData.startsWith('UEsDBBQ')) {
          mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          extension = '.docx';
        } else if (advertData.startsWith('/9j/')) {
          mimeType = 'image/jpeg';
          extension = '.jpg';
        }

        const blob = new Blob([uint8Array], { type: mimeType });
        const blobUrl = URL.createObjectURL(blob);

        this.store.setAdvertMetadata({
          name: `advertisement${extension}`,
          size: uint8Array.length,
          download_url: blobUrl,
          preview_url: blobUrl,
          mime_type: mimeType,
          file_path: advertData,
          is_base64: true
        });
      } catch (error) {
        console.error("Error processing Base64 advertisement data:", error);
        this.store.setAdvertMetadata({
          name: 'advertisement.pdf',
          size: 0,
          download_url: `/comperative_schedule/api/files/download/${advertData}`,
          preview_url: `/comperative_schedule/api/files/preview/${advertData}`,
          mime_type: 'application/pdf',
          file_path: advertData
        });
      }
    } else {
      this.store.setAdvertMetadata({
        name: 'advertisement.pdf',
        size: 0,
        download_url: `/comperative_schedule/api/files/download/${advertData}`,
        preview_url: `/comperative_schedule/api/files/preview/${advertData}`,
        mime_type: 'application/pdf',
        file_path: advertData
      });
    }
  }

  // === VALIDATION ===

  /**
   * Validate schedule fields
   */
  validateScheduleFields(): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Basic validation - can be enhanced later
    errors.push("Validation not fully implemented yet");
    
    return { isValid: errors.length === 0, errors };
  }

  /**
   * Validate bid form
   */
  validateBidForm(bid: IBid): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (!bid.supplier_name) errors.push("Please select a supplier");
    if (!bid.bid_date) errors.push("Please select a bid date");
    if (!bid.bid_document && !bid.encoded_bid_document && !bid.bid_document_url) {
      errors.push("Please select a bid document");
    }
    
    if (!bid.items || bid.items.length === 0) {
      errors.push("Please add at least one item to the bid");
    } else {
      bid.items.forEach((item) => {
        if (!item.quantity) errors.push(`Item "${item.item_required}": Quantity is required`);
        if (!item.unit_price) errors.push(`Item "${item.item_required}": Unit price is required`);
        if (!item.unit_of_measurement) errors.push(`Item "${item.item_required}": Unit of measurement is required`);
        if (!item.vat) errors.push(`Item "${item.item_required}": VAT selection is required`);
      });
    }
    
    return { isValid: errors.length === 0, errors };
  }

  /**
   * Validate file
   */
  validateFile(file: File): { isValid: boolean; error?: string } {
    const allowedTypes = [
      'application/pdf',
      'application/msword', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/jpg', 
      'image/png'
    ];
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
      return { 
        isValid: false, 
        error: 'File type not allowed. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG files only.' 
      };
    }
    
    if (file.size > maxSize) {
      return { 
        isValid: false, 
        error: 'File size too large. Maximum allowed size is 10MB.' 
      };
    }
    
    return { isValid: true };
  }

  // === UTILITY METHODS ===

  /**
   * Get API service instance
   */
  getApiService(): ScheduleApiService {
    return this.apiService;
  }

  /**
   * Refresh CSRF token
   */
  refreshCsrfToken(): void {
    this.apiService.refreshCsrfToken();
  }

  /**
   * Check API health
   */
  async checkApiHealth(): Promise<boolean> {
    return await this.apiService.healthCheck();
  }
}

export default ScheduleBusinessLogic;
