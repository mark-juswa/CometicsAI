import type { LookDetails } from '../lib/business/look-information';
import {
  pgTable,
  uuid,
  text,
  boolean,
  timestamp,
  varchar,
  integer,
  numeric,
  jsonb,
  pgEnum,
  bigint,
  index,
  uniqueIndex,
  primaryKey,
  foreignKey,
  check,
} from 'drizzle-orm/pg-core';
import { relations, sql } from 'drizzle-orm';

// ─── Enums ──────────────────────────────────────────────────────────────────
export const userRoleEnum = pgEnum('user_role', ['admin', 'stylist', 'client']);
export const appointmentStatusEnum = pgEnum('appointment_status', [
  'pending',
  'confirmed',
  'completed',
  'cancelled',
  'in_progress',
  'no_show',
]);
export const productStatusEnum = pgEnum('product_status', [
  'in_stock',
  'low_stock',
  'out_of_stock',
]);
export const styleTypeEnum = pgEnum('style_type', ['hair', 'nail', 'makeup']);

// ─── Users ──────────────────────────────────────────────────────────────────
export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  name: varchar('name', { length: 255 }).notNull(),
  passwordHash: text('password_hash').notNull(),
  role: userRoleEnum('role').notNull().default('client'),
  avatar: text('avatar'),
  phone: varchar('phone', { length: 40 }),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── Client Profiles ────────────────────────────────────────────────────────
export const clientProfiles = pgTable('client_profiles', {
  userId: uuid('user_id')
    .primaryKey()
    .references(() => users.id, { onDelete: 'cascade' }),
  hairPreferences: text('hair_preferences'),
  nailPreferences: text('nail_preferences'),
  styleHistory: jsonb('style_history').$type<
    Array<{
      date: string;
      type: 'hair' | 'nail';
      description: string;
    }>
  >(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── Appointments ───────────────────────────────────────────────────────────
export const appointments = pgTable(
  'appointments',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    clientId: uuid('client_id')
      .notNull()
      .references(() => users.id, { onDelete: 'cascade' }),
    stylistId: uuid('stylist_id').references(() => users.id, { onDelete: 'set null' }),
    serviceName: varchar('service_name', { length: 255 }).notNull(),
    serviceType: varchar('service_type', { length: 100 }).notNull(),
    appointmentDate: timestamp('appointment_date').notNull(),
    durationMinutes: integer('duration_minutes').notNull().default(90),
    status: appointmentStatusEnum('status').notNull().default('pending'),
    totalPrice: integer('total_price'),
    notes: text('notes'),
    completedAt: timestamp('completed_at', { withTimezone: true }),
    completedBy: uuid('completed_by').references(() => users.id),
    aiGenerationId: uuid('ai_generation_id'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.aiGenerationId, table.clientId],
      foreignColumns: [aiGenerations.id, aiGenerations.clientId],
      name: 'appointments_look_owner_fk',
    }),
    index('appointments_stylist_date_idx').on(table.stylistId, table.appointmentDate),
    index('appointments_date_status_idx').on(table.appointmentDate, table.status),
    index('appointments_look_idx').on(table.aiGenerationId),
    index('appointments_completed_by_idx').on(table.completedBy),
    check('appointment_duration_positive', sql`${table.durationMinutes} BETWEEN 1 AND 1440`),
  ],
);

// ─── Inventory ──────────────────────────────────────────────────────────────
export const inventory = pgTable('inventory', {
  id: uuid('id').primaryKey().defaultRandom(),
  productName: varchar('product_name', { length: 255 }).notNull(),
  brand: varchar('brand', { length: 120 }),
  category: varchar('category', { length: 100 }).notNull(),
  currentStock: integer('current_stock').notNull().default(0),
  minimumThreshold: integer('minimum_threshold').notNull().default(10),
  unitPrice: integer('unit_price'),
  status: productStatusEnum('status').notNull().default('in_stock'),
  lastRestocked: timestamp('last_restocked'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// Stylist qualifications are stored as salon service groups, never inferred from names.
export const stylistSpecialties = pgTable('stylist_specialties', {
  stylistId: uuid('stylist_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  serviceType: varchar('service_type', { length: 40 }).notNull(),
}, (t) => [
  primaryKey({ name: 'stylist_specialties_pkey', columns: [t.stylistId, t.serviceType] }),
  check('stylist_specialties_type_check', sql`${t.serviceType} IN ('hair','nail','makeup','treatment','massage','aesthetic')`),
]);

export const inventoryTransactions = pgTable('inventory_transactions', {
  id: uuid('id').primaryKey().defaultRandom(),
  inventoryId: uuid('inventory_id').references(() => inventory.id, { onDelete: 'set null' }),
  productName: varchar('product_name', { length: 255 }).notNull(),
  direction: varchar('direction', { length: 3 }).notNull(),
  quantity: integer('quantity').notNull(),
  stockAfter: integer('stock_after').notNull(),
  note: varchar('note', { length: 500 }),
  recordedBy: uuid('recorded_by').notNull().references(() => users.id),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => [
  index('inventory_transactions_item_created_idx').on(t.inventoryId, t.createdAt.desc()),
  check('inventory_transactions_direction_check', sql`${t.direction} IN ('in','out')`),
  check('inventory_transactions_quantity_check', sql`${t.quantity} > 0`),
  check('inventory_transactions_stock_check', sql`${t.stockAfter} >= 0`),
]);

// ─── AI Generations ─────────────────────────────────────────────────────────
export const aiGenerations = pgTable(
  'ai_generations',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    clientId: uuid('client_id')
      .notNull()
      .references(() => users.id, { onDelete: 'cascade' }),
    sourceImageUrl: text('source_image_url'),
    promptText: text('prompt_text'),
    generatedImageUrl: text('generated_image_url'),
    styleId: varchar('style_id', { length: 80 }),
    styleName: varchar('style_name', { length: 255 }),
    savedAt: timestamp('saved_at', { withTimezone: true }),
    resultHash: varchar('result_hash', { length: 64 }),
    imageBytes: integer('image_bytes'),
    sourceKind: varchar('source_kind', { length: 20 }).notNull().default('legacy'),
    lookDetails: jsonb('look_details').$type<LookDetails>(),
    styleType: styleTypeEnum('style_type').notNull(),
    analysisResult: jsonb('analysis_result').$type<{
      category: 'hair' | 'nails';
      currentAttributes: {
        shapeOrCut: string;
        color: string;
        condition: string;
      };
      recommendations: Array<{
        title: string;
        colorPalette: string;
        designDetails: string;
        reasoning: string;
        generationPrompt: string;
      }>;
    }>(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex('ai_generations_id_owner_idx').on(table.id, table.clientId),
    uniqueIndex('ai_generations_saved_dedup_idx').on(
      table.clientId,
      table.styleType,
      table.styleId,
      table.resultHash,
    ),
    index('ai_generations_client_saved_idx').on(table.clientId, table.savedAt.desc(), table.id),
    check(
      'saved_look_integrity',
      sql`${table.resultHash} IS NULL OR (${table.resultHash} ~ '^[0-9a-f]{64}$' AND ${table.styleId} IS NOT NULL AND ${table.styleName} IS NOT NULL AND ${table.generatedImageUrl} IS NOT NULL AND ${table.imageBytes} IS NOT NULL AND ${table.imageBytes} BETWEEN 1 AND 8388608 AND ${table.sourceKind} IN ('manual','consultation'))`,
    ),
  ],
);

// Actual consumption is a service record, not an automatic stock adjustment.
export const appointmentReviews = pgTable(
  'appointment_reviews',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    appointmentId: uuid('appointment_id')
      .notNull()
      .unique()
      .references(() => appointments.id, { onDelete: 'restrict' }),
    clientId: uuid('client_id')
      .notNull()
      .references(() => users.id),
    stylistId: uuid('stylist_id')
      .notNull()
      .references(() => users.id),
    rating: integer('rating').notNull(),
    comment: varchar('comment', { length: 1000 }),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [
    check('review_rating_range', sql`${t.rating} BETWEEN 1 AND 5`),
    index('appointment_reviews_client_idx').on(t.clientId),
    index('appointment_reviews_stylist_idx').on(t.stylistId),
  ],
);
export const appointmentProductUsage = pgTable(
  'appointment_product_usage',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    appointmentId: uuid('appointment_id')
      .notNull()
      .references(() => appointments.id, { onDelete: 'restrict' }),
    inventoryId: uuid('inventory_id').references(() => inventory.id, { onDelete: 'set null' }),
    productName: varchar('product_name', { length: 255 }).notNull(),
    brand: varchar('brand', { length: 120 }),
    quantity: numeric('quantity', { precision: 12, scale: 3, mode: 'number' }),
    unit: varchar('unit', { length: 32 }),
    unitCost: numeric('unit_cost', { precision: 12, scale: 2, mode: 'number' }),
    recordedBy: uuid('recorded_by')
      .notNull()
      .references(() => users.id),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [
    index('appointment_product_usage_appointment_idx').on(t.appointmentId),
    index('appointment_product_usage_inventory_idx').on(t.inventoryId),
    index('appointment_product_usage_recorder_idx').on(t.recordedBy),
    check('usage_quantity_positive', sql`${t.quantity} > 0 AND ${t.quantity} <= 1000000`),
    check('usage_cost_nonnegative', sql`${t.unitCost} >= 0 AND ${t.unitCost} <= 1000000`),
    check('usage_quantity_unit', sql`${t.quantity} IS NULL OR ${t.unit} IS NOT NULL`),
    check('usage_product_name', sql`length(trim(${t.productName})) > 0`),
    check(
      'usage_cost_basis',
      sql`${t.unitCost} IS NULL OR (${t.quantity} IS NOT NULL AND ${t.unit} IS NOT NULL)`,
    ),
  ],
);

// ─── Relations ──────────────────────────────────────────────────────────────
export const usersRelations = relations(users, ({ one, many }) => ({
  profile: one(clientProfiles, {
    fields: [users.id],
    references: [clientProfiles.userId],
  }),
  clientAppointments: many(appointments, { relationName: 'clientAppointments' }),
  stylistAppointments: many(appointments, { relationName: 'stylistAppointments' }),
  generations: many(aiGenerations),
  specialties: many(stylistSpecialties),
}));

export const clientProfilesRelations = relations(clientProfiles, ({ one }) => ({
  user: one(users, {
    fields: [clientProfiles.userId],
    references: [users.id],
  }),
}));

export const stylistSpecialtiesRelations = relations(stylistSpecialties, ({ one }) => ({
  stylist: one(users, { fields: [stylistSpecialties.stylistId], references: [users.id] }),
}));

export const appointmentsRelations = relations(appointments, ({ one }) => ({
  look: one(aiGenerations, {
    fields: [appointments.aiGenerationId],
    references: [aiGenerations.id],
  }),
  client: one(users, {
    fields: [appointments.clientId],
    references: [users.id],
    relationName: 'clientAppointments',
  }),
  stylist: one(users, {
    fields: [appointments.stylistId],
    references: [users.id],
    relationName: 'stylistAppointments',
  }),
}));

export const aiGenerationsRelations = relations(aiGenerations, ({ one }) => ({
  client: one(users, {
    fields: [aiGenerations.clientId],
    references: [users.id],
  }),
}));

// ─── Inferred Types ─────────────────────────────────────────────────────────
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type ClientProfile = typeof clientProfiles.$inferSelect;
export type NewClientProfile = typeof clientProfiles.$inferInsert;
export type Appointment = typeof appointments.$inferSelect;
export type NewAppointment = typeof appointments.$inferInsert;
export type InventoryItem = typeof inventory.$inferSelect;
export type NewInventoryItem = typeof inventory.$inferInsert;
export type AiGeneration = typeof aiGenerations.$inferSelect;
export type NewAiGeneration = typeof aiGenerations.$inferInsert;

export type UserRole = (typeof userRoleEnum.enumValues)[number];
export type AppointmentStatus = (typeof appointmentStatusEnum.enumValues)[number];
export type ProductStatus = (typeof productStatusEnum.enumValues)[number];
export type StyleType = (typeof styleTypeEnum.enumValues)[number];

// Server-only endpoint metadata for the scheduled Kaggle demonstration.
export const stylistWorkSettings = pgTable('stylist_work_settings', {
  stylistId: uuid('stylist_id').primaryKey().references(() => users.id), available: boolean('available').notNull().default(false),
  hours: jsonb('hours').$type<{ day: number; start: string; end: string }[]>().notNull().default([]),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
});
export const clientConsultations = pgTable('client_consultations', {
  id: uuid('id').primaryKey().defaultRandom(), clientId: uuid('client_id').notNull().references(() => users.id),
  sourceKey: varchar('source_key', { length: 64 }).notNull(), feature: varchar('feature', { length: 20 }).notNull(),
  snapshot: jsonb('snapshot').notNull().default({}), createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, t => [uniqueIndex('client_consultations_source_idx').on(t.clientId,t.sourceKey),uniqueIndex('client_consultations_id_owner_idx').on(t.id,t.clientId),check('client_consultations_feature_check',sql`${t.feature} IN ('hairstyle','nails','makeup')`)]);
export const clientReferenceImages = pgTable('client_reference_images', {
  id: uuid('id').primaryKey().defaultRandom(),clientId: uuid('client_id').notNull().references(() => users.id),consultationId: uuid('consultation_id').notNull(),imageData: text('image_data').notNull(),
  imageHash: varchar('image_hash',{length:64}).notNull(),imageBytes: integer('image_bytes').notNull(),contentType: text('content_type').notNull(),width: integer('width').notNull(),height: integer('height').notNull(),
  filename: varchar('filename',{length:255}).notNull(),createdAt: timestamp('created_at',{withTimezone:true}).notNull().defaultNow(),
},t=>[foreignKey({columns:[t.consultationId,t.clientId],foreignColumns:[clientConsultations.id,clientConsultations.clientId]}),uniqueIndex('client_reference_images_session_hash_idx').on(t.consultationId,t.imageHash),index('client_reference_images_owner_idx').on(t.clientId,t.createdAt.desc(),t.id)]);
export const clientConsultationResults = pgTable('client_consultation_results',{
  consultationId:uuid('consultation_id').notNull(),clientId:uuid('client_id').notNull(),recommendationId:varchar('recommendation_id',{length:80}).notNull(),generationId:uuid('generation_id').notNull(),
  createdAt:timestamp('created_at',{withTimezone:true}).notNull().defaultNow(),
},t=>[primaryKey({columns:[t.consultationId,t.recommendationId,t.generationId]}),foreignKey({columns:[t.consultationId,t.clientId],foreignColumns:[clientConsultations.id,clientConsultations.clientId]}),foreignKey({columns:[t.generationId,t.clientId],foreignColumns:[aiGenerations.id,aiGenerations.clientId]})]);
export const clientConsultationJobs = pgTable('client_consultation_jobs',{
  jobId:uuid('job_id').primaryKey(),clientId:uuid('client_id').notNull(),consultationId:uuid('consultation_id').notNull(),recommendationId:varchar('recommendation_id',{length:80}).notNull(),
},t=>[foreignKey({columns:[t.consultationId,t.clientId],foreignColumns:[clientConsultations.id,clientConsultations.clientId]})]);
export const appointmentPayments = pgTable('appointment_payments',{
  id:uuid('id').primaryKey().defaultRandom(),appointmentId:uuid('appointment_id').notNull().references(()=>appointments.id,{onDelete:'restrict'}),amount:integer('amount').notNull(),method:varchar('method',{length:20}).notNull(),reference:varchar('reference',{length:160}),
  requestId:uuid('request_id').notNull().unique(),recordedBy:uuid('recorded_by').notNull().references(()=>users.id),createdAt:timestamp('created_at',{withTimezone:true}).notNull().defaultNow(),
},t=>[index('appointment_payments_appointment_idx').on(t.appointmentId,t.createdAt),check('appointment_payments_amount_check',sql`${t.amount} BETWEEN 1 AND 100000000`),check('appointment_payments_method_check',sql`${t.method} IN ('cash','card','bank','other')`)]);

export const aiRuntimeEndpoints = pgTable('ai_runtime_endpoints', {
  slot: text('slot').primaryKey(),
  sessionId: uuid('session_id').notNull(),
  endpoint: varchar('endpoint', { length: 256 }).notNull(),
  startedAt: bigint('started_at', { mode: 'number' }).notNull(),
  lastIssuedAt: bigint('last_issued_at', { mode: 'number' }).notNull(),
  leaseExpiresAt: timestamp('lease_expires_at', { withTimezone: true }).notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
});

/** Guest allowance metadata only. Explicit migration 0006 also installs atomic admission. */
export const aiGuestTrials = pgTable('ai_guest_trials', {
  tokenHash: text('token_hash').primaryKey(),
  ownerId: text('owner_id').notNull().unique(),
  networkTag: text('network_tag').notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
  state: text('state').default('available').notNull(),
  counters: jsonb('counters').default({}).notNull(),
  operationId: uuid('operation_id'),
  consultationId: uuid('consultation_id'),
  consultationExpiresAt: timestamp('consultation_expires_at', { withTimezone: true }),
  recommendationId: text('recommendation_id'),
  jobId: uuid('job_id'),
  attemptAt: timestamp('attempt_at', { withTimezone: true }),
}, t => [
  index('ai_guest_trials_network_created_idx').on(t.networkTag, t.createdAt),
  index('ai_guest_trials_updated_idx').on(t.updatedAt),
  index('ai_guest_trials_attempt_idx').on(t.attemptAt).where(sql`${t.attemptAt} IS NOT NULL`),
  check('ai_guest_trials_token_hash_check', sql`${t.tokenHash} ~ '^[a-f0-9]{64}$'`),
  check('ai_guest_trials_owner_id_check', sql`${t.ownerId} ~ '^guest_[a-f0-9]{32}$'`),
  check('ai_guest_trials_network_tag_check', sql`${t.networkTag} ~ '^[a-f0-9]{64}$'`),
  check('ai_guest_trials_state_check', sql`${t.state} IN ('available','reserved','spent')`),
]);

export const salonServices = pgTable('salon_services', { id:text('id').primaryKey(),name:text('name').notNull(),serviceType:text('service_type').notNull(),groupId:text('group_id').notNull(),groupLabel:text('group_label').notNull(),price:text('price').notNull(),active:boolean('active').notNull().default(true) });
export const presetServices = pgTable('preset_services',{feature:text('feature').notNull(),styleId:text('style_id').notNull(),serviceId:text('service_id').notNull().references(()=>salonServices.id)},t=>[primaryKey({columns:[t.feature,t.styleId]})]);
export const appointmentServices = pgTable('appointment_services',{appointmentId:uuid('appointment_id').primaryKey().references(()=>appointments.id,{onDelete:'cascade'}),serviceId:text('service_id').notNull().references(()=>salonServices.id)});

export const appointmentLifecyclePolicy=pgTable('appointment_lifecycle_policy',{id:boolean('id').primaryKey().default(true),enabledAt:timestamp('enabled_at',{withTimezone:true}).notNull().defaultNow()});
export const appointmentServiceTracking=pgTable('appointment_service_tracking',{appointmentId:uuid('appointment_id').primaryKey().references(()=>appointments.id,{onDelete:'cascade'}),arrivedAt:timestamp('arrived_at',{withTimezone:true}),startedAt:timestamp('started_at',{withTimezone:true}),endedAt:timestamp('ended_at',{withTimezone:true}),noShowAt:timestamp('no_show_at',{withTimezone:true}),noShowBy:uuid('no_show_by').references(()=>users.id),releaseAt:timestamp('release_at',{withTimezone:true}),lastActor:uuid('last_actor').references(()=>users.id),stopReason:text('stop_reason'),explanation:varchar('explanation',{length:1000})});
export const appointmentActivity=pgTable('appointment_activity',{id:uuid('id').primaryKey().defaultRandom(),appointmentId:uuid('appointment_id').notNull().references(()=>appointments.id,{onDelete:'cascade'}),action:text('action').notNull(),previousStatus:text('previous_status'),status:text('status').notNull(),actorId:uuid('actor_id').references(()=>users.id),source:text('source').notNull(),happenedAt:timestamp('happened_at',{withTimezone:true}).notNull().defaultNow(),explanation:varchar('explanation',{length:1000}),details:jsonb('details').notNull().default({})});
