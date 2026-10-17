import {
  pgTable,
  uuid,
  text,
  timestamp,
  varchar,
  integer,
  jsonb,
  pgEnum,
  bigint,
  index,
  uniqueIndex,
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
    status: appointmentStatusEnum('status').notNull().default('pending'),
    totalPrice: integer('total_price'),
    notes: text('notes'),
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
  ],
);

// ─── Inventory ──────────────────────────────────────────────────────────────
export const inventory = pgTable('inventory', {
  id: uuid('id').primaryKey().defaultRandom(),
  productName: varchar('product_name', { length: 255 }).notNull(),
  category: varchar('category', { length: 100 }).notNull(),
  currentStock: integer('current_stock').notNull().default(0),
  minimumThreshold: integer('minimum_threshold').notNull().default(10),
  unitPrice: integer('unit_price'),
  status: productStatusEnum('status').notNull().default('in_stock'),
  lastRestocked: timestamp('last_restocked'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

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

// ─── Relations ──────────────────────────────────────────────────────────────
export const usersRelations = relations(users, ({ one, many }) => ({
  profile: one(clientProfiles, {
    fields: [users.id],
    references: [clientProfiles.userId],
  }),
  clientAppointments: many(appointments, { relationName: 'clientAppointments' }),
  stylistAppointments: many(appointments, { relationName: 'stylistAppointments' }),
  generations: many(aiGenerations),
}));

export const clientProfilesRelations = relations(clientProfiles, ({ one }) => ({
  user: one(users, {
    fields: [clientProfiles.userId],
    references: [users.id],
  }),
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
export const aiRuntimeEndpoints = pgTable('ai_runtime_endpoints', {
  slot: text('slot').primaryKey(),
  sessionId: uuid('session_id').notNull(),
  endpoint: varchar('endpoint', { length: 256 }).notNull(),
  startedAt: bigint('started_at', { mode: 'number' }).notNull(),
  lastIssuedAt: bigint('last_issued_at', { mode: 'number' }).notNull(),
  leaseExpiresAt: timestamp('lease_expires_at', { withTimezone: true }).notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
});
