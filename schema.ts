import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  password: text('password').notNull(),
  email: text('email').notNull(),
  username: text('username').notNull(),
  first_name: text('first_name').notNull(),
  last_name: text('last_name').notNull(),
  phone: text('phone').notNull(),
  role: text('role').notNull(),
  status: text('status').notNull(),
  access_token: text('access_token').notNull(),
  refresh_token: text('refresh_token').notNull(),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull(),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const inspectionReports = sqliteTable('inspection_reports', {
  id: text('id').primaryKey(),
  
  // Basic Information
  inspection_date: text('inspection_date'),
  service_no: text('service_no'),
  installation_type: text('installation_type'),
  consumer_name: text('consumer_name'),
  property_supplied: text('property_supplied'),
  property_owner_name: text('property_owner_name'),
  property_owner_address: text('property_owner_address'),
  contractor: text('contractor'),
  contractor_address: text('contractor_address'),
  
  // Installation Details
  size_of_mains: text('size_of_mains'),
  size_of_mains_conduit: text('size_of_mains_conduit'),
  earthing: text('earthing'),
  consumer_unit_type: text('consumer_unit_type'),
  db_enclosure_type: text('db_enclosure_type'),
  
  // Testing
  insulation_resistance_between: text('insulation_resistance_between'),
  insulation_resistance_to_earth: text('insulation_resistance_to_earth'),
  continuity_test: text('continuity_test'),
  
  // Safety Checks
  earth_fault_protection: text('earth_fault_protection'),
  overcurrent_protection: text('overcurrent_protection'),
  installation_safety: text('installation_safety'),
  
  // Conduits
  conduit_material: text('conduit_material'),
  conduit_installation: text('conduit_installation'),
  
  // Final Checks
  overall_compliance: text('overall_compliance'),
  defects_found: text('defects_found'),
  inspector_comments: text('inspector_comments'),
  
  // Derived status (calculated from safety checks)
  status: text('status'), // 'pass', 'fail', 'pending'
  
  // Link to client application (if started from application)
  client_application_id: text('client_application_id').references(() => clientApplications.id),
  
  // Metadata
  inspector_id: text('inspector_id').references(() => users.id),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull(),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const clientApplications = sqliteTable('client_applications', {
  id: text('id').primaryKey(),
  
  // Application Information
  application_number: text('application_number').notNull(),
  application_type: text('application_type').notNull(), // 'new_installation', 'routine_inspection', 'change_of_tenancy', 'reconnection'
  priority: text('priority').notNull().default('normal'), // 'low', 'normal', 'high', 'urgent'
  
  // Customer Information
  customer_name: text('customer_name').notNull(),
  customer_phone: text('customer_phone'),
  customer_email: text('customer_email'),
  customer_address: text('customer_address'),
  
  // Property Information
  property_address: text('property_address').notNull(),
  property_type: text('property_type'), // 'residential', 'commercial', 'industrial'
  service_number: text('service_number'),
  
  // Installation Details
  installation_description: text('installation_description'),
  contractor_name: text('contractor_name'),
  contractor_license: text('contractor_license'),
  
  // Application Status
  status: text('status').notNull().default('submitted'), // 'submitted', 'assigned', 'in_progress', 'completed', 'rejected'
  
  // Client Liaison Information
  submitted_by: text('submitted_by').references(() => users.id), // Client liaison officer
  submission_date: integer('submission_date', { mode: 'timestamp' }).notNull(),
  
  // Additional Information
  notes: text('notes'),
  documents_attached: integer('documents_attached', { mode: 'boolean' }).default(false),
  
  // Metadata
  created_at: integer('created_at', { mode: 'timestamp' }).notNull(),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const applicationAssignments = sqliteTable('application_assignments', {
  id: text('id').primaryKey(),
  
  // Assignment Information
  application_id: text('application_id').references(() => clientApplications.id).notNull(),
  assigned_to: text('assigned_to').references(() => users.id).notNull(), // Field officer/inspector
  assigned_by: text('assigned_by').references(() => users.id).notNull(), // Foreman
  
  // Assignment Details
  assignment_date: integer('assignment_date', { mode: 'timestamp' }).notNull(),
  due_date: integer('due_date', { mode: 'timestamp'}),
  assignment_notes: text('assignment_notes'),
  
  // Status
  status: text('status').notNull().default('assigned'), // 'assigned', 'accepted', 'in_progress', 'completed'
  
  // Acceptance/Completion
  accepted_date: integer('accepted_date', { mode: 'timestamp'}),
  completed_date: integer('completed_date', { mode: 'timestamp'}),
  completion_notes: text('completion_notes'),
  
  // Metadata
  created_at: integer('created_at', { mode: 'timestamp' }).notNull(),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull(),
});