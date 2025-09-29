/**
 * TypeScript interfaces for BEApp Mobile Sync API
 *
 * These types ensure type safety when integrating with the sync API
 * Copy these interfaces to your mobile app's type definitions
 */

// Base response interface
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  code?: string;
}

// Authentication types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// Inspection data interfaces
export interface InspectionData {
  id?: string;
  consumer_name: string;
  inspection_date: string; // ISO date string
  service_no?: string;
  reason_for_inspection?: 'new_installation' | 'routine' | 'change_of_tenancy';
  property_supplied?: string;
  property_owner_name?: string;
  property_owner_address?: string;
  contractor?: string;
  contractor_address?: string;
  size_of_mains?: string;
  size_of_mains_conduit?: string;
  consumer_main_switch_type?: string;
  consumer_main_switch_capacity?: string;
  consumer_main_switch_setting?: string;
  neutrals_fused?: SafetyCheckValue;
  neutral_block_fitted?: SafetyCheckValue;
  earth_electrode_installed?: SafetyCheckValue;
  earth_electrode_type?: string;
  all_equipment_bonded_earthed: SafetyCheckValue;
  insulation_resistance_between?: string;
  insulation_resistance_to_earth?: string;
  earth_continuity_resistance?: string;
  polarity_switches_plugs?: string;
  socket_outlets_earthed: SafetyCheckValue;
  socket_outlet_type?: string;
  wiring_type?: string;
  circuit_conductors_correct_size: SafetyCheckValue;
  wiring_condition?: string;
  flexible_cord_prohibited_positions?: string;
  bathroom_switch_accessible?: SafetyCheckValue;
  unearthed_metal_switches?: string;
  conduits_bushed?: SafetyCheckValue;
  conduits_bonded_earth?: SafetyCheckValue;
  conduits_correct_size?: SafetyCheckValue;
  conduits_adequately_supported?: SafetyCheckValue;
  conduits_suitable_type?: SafetyCheckValue;
  max_lighting_points_per_circuit?: number;
  max_plug_points_per_circuit?: number;
  total_lighting_points?: number;
  total_plug_points?: number;
  appliances_wattages?: string;
  motors_plant_details?: string;
  overhead_lines_height?: SafetyCheckValue;
  overhead_lines_conductor_size?: SafetyCheckValue;
  overhead_lines_support?: SafetyCheckValue;
  overhead_lines_general?: SafetyCheckValue;
  overhead_earthwires_fitted?: SafetyCheckValue;
  overhead_lines_protected?: SafetyCheckValue;
  outbuildings_protected?: SafetyCheckValue;
  motor_installations_protected?: SafetyCheckValue;
  commission_switch_details?: string;
  supply_connected_disconnected?: string;
  contractor_notified_defects?: SafetyCheckValue;
  other_features_attention?: string;
  status: InspectionStatus;
  client_application_id: string;
  created_at?: string;
  updated_at?: string;
}

export type SafetyCheckValue = 'pass' | 'fail' | 'na';
export type InspectionStatus = 'pending' | 'in_progress' | 'completed' | 'approved' | 'rejected';

// Batch operations
export interface InspectionBatchRequest {
  inspections: InspectionData[];
}

export interface InspectionBatchResponse {
  success: boolean;
  results: {
    processed: number;
    successful: number;
    failed: number;
    errors: Array<{
      index: number;
      errors: string[];
    }>;
  };
}

// Download operations
export interface InspectionDownloadRequest {
  ids: string[];
}

export interface InspectionDownloadResponse {
  success: boolean;
  inspections: InspectionData[];
  count: number;
}

// Incremental sync
export interface IncrementalSyncRequest {
  since_timestamp: string; // ISO datetime string
}

export interface IncrementalSyncResponse {
  success: boolean;
  records_processed: number;
  conflicts_resolved: number;
  errors: string[];
}

// Conflict resolution
export interface ConflictData {
  id: string;
  conflict_type: 'inspection_data' | 'workflow_state' | 'assignment' | 'assignment_status' | 'approval' | 'approval_state' | 'photo_metadata';
  entity_type: string;
  entity_id: string;
  local_data: Record<string, any>;
  server_data: Record<string, any>;
  resolution: 'manual' | 'server_wins' | 'local_wins' | 'merged';
  resolved_data?: Record<string, any>;
  resolved_by?: string;
  resolved_at?: string;
  notes?: string;
  sync_operation: string;
}

export interface ConflictListResponse {
  success: boolean;
  conflicts: ConflictData[];
  count: number;
}

export interface ConflictResolutionRequest {
  resolution: 'server_wins' | 'local_wins' | 'merged';
  resolved_data?: Record<string, any>;
  notes?: string;
}

export interface ConflictResolutionResponse {
  success: boolean;
  conflict: ConflictData;
}

// Sync status and dashboard
export interface SyncStatusSummary {
  recent_syncs_count: number;
  successful_syncs_count: number;
  success_rate: number;
  pending_uploads: number;
  unresolved_conflicts: number;
  last_sync: string | null;
  sync_health: 'good' | 'warning' | 'critical';
}

export interface SyncOperation {
  id: string;
  operation_type: 'full' | 'incremental' | 'upload' | 'download';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  user: string;
  records_affected: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration?: number;
  metadata: Record<string, any>;
  last_sync_timestamp?: string;
  sync_direction: 'upload' | 'download' | 'both';
}

export interface SyncDashboardData {
  recent_syncs: SyncOperation[];
  pending_uploads: number;
  unresolved_conflicts: number;
  statistics: {
    total_syncs: number;
    successful_syncs: number;
    failed_syncs: number;
    success_rate: number;
  };
}

// Sync service class interface
export interface SyncServiceConfig {
  baseUrl: string;
  token: string;
  timeout?: number;
  retries?: number;
}

export interface SyncResult {
  success: boolean;
  action?: 'created' | 'updated';
  inspection_id?: string;
  sync_operation?: string;
  errors?: string[];
  message?: string;
}

// Error types
export class SyncError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'SyncError';
  }
}

export class ValidationError extends SyncError {
  constructor(message: string, details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class ConflictError extends SyncError {
  constructor(message: string, public conflict: ConflictData) {
    super(message, 'CONFLICT_DETECTED', 422, { conflict });
    this.name = 'ConflictError';
  }
}

// Assignment data interfaces
export interface AssignmentData {
  id?: string;
  application: string; // UUID
  assigned_to: string; // UUID
  assigned_by: string; // UUID
  assignment_date: string; // ISO datetime
  due_date?: string; // ISO datetime
  assignment_notes?: string;
  status: 'assigned' | 'accepted' | 'in_progress' | 'completed';
  accepted_date?: string; // ISO datetime
  completed_date?: string; // ISO datetime
  completion_notes?: string;
  created_at?: string;
  updated_at?: string;
}

// Approval data interfaces
export interface ApprovalData {
  id?: string;
  step: number;
  user: string; // UUID
  process: string; // UUID
  comment?: string;
  approved?: 'Approved' | 'Rejected';
  approved_at?: string; // ISO datetime
}

// Batch operations
export interface AssignmentBatchRequest {
  assignments: AssignmentData[];
  operation_type: 'bulk_create' | 'bulk_update' | 'bulk_status_change';
}

export interface AssignmentBatchResponse {
  success: boolean;
  results: {
    processed: number;
    successful: number;
    failed: number;
    errors: Array<{
      index: number;
      errors: string[];
    }>;
  };
}

// Approval transitions
export interface ApprovalTransitionRequest {
  process_id: string; // UUID
  step_id: number;
  action: 'approve' | 'reject' | 'request_changes';
  comment?: string;
}

export interface ApprovalTransitionResponse {
  success: boolean;
  action: string;
  approval: ApprovalData;
  sync_operation?: string;
}

// Merge operations
export interface MergeOperationRequest {
  entity_type: string;
  entity_id: string; // UUID
  merge_strategy: 'server_wins' | 'local_wins' | 'intelligent_merge' | 'manual_merge';
  conflict_fields?: string[];
  resolved_data?: Record<string, any>;
}

export interface BulkMergeRequest {
  operations: MergeOperationRequest[];
}

export interface BulkMergeResponse {
  success: boolean;
  results: {
    processed: number;
    successful: number;
    failed: number;
    errors: Array<{
      index: number;
      errors: string[];
    }>;
  };
  sync_operation?: string;
}

export interface IntelligentMergeSuggestionRequest {
  entity_type: string;
  entity_id: string; // UUID
  local_data: Record<string, any>;
  server_data: Record<string, any>;
}

export interface IntelligentMergeSuggestionResponse {
  success: boolean;
  suggestion: {
    suggested_resolution: 'server_wins' | 'local_wins' | 'merged';
    confidence_score: number;
    reasoning: string;
    suggested_merged_data?: Record<string, any>;
  };
}

// Utility types
export type SyncPriority = 'low' | 'normal' | 'high' | 'critical';

export interface QueuedOperation {
  id: string;
  type: 'inspection_create' | 'inspection_update' | 'photo_upload' | 'workflow_update' | 'assignment_create' | 'assignment_update' | 'assignment_accept' | 'assignment_complete' | 'approval_create' | 'approval_update' | 'approval_transition' | 'merge_operation';
  data: any;
  priority: SyncPriority;
  created_at: string;
  attempts: number;
  max_attempts: number;
}

// Event types for real-time updates
export interface SyncEvent {
  type: 'sync_started' | 'sync_completed' | 'sync_failed' | 'conflict_detected';
  data: any;
  timestamp: string;
}

export interface SyncProgress {
  operation_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number; // 0-100
  message?: string;
  records_processed?: number;
  total_records?: number;
}
