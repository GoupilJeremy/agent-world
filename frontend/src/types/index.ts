/**
 * Agent World - Global Types
 * Types TypeScript globaux pour l'application
 */

// API Response Types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp?: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  description?: string;
  model: string;
  status: AgentStatus;
  createdAt: string;
  updatedAt: string;
  version?: string;
  author?: string;
  tags?: string[];
  configuration?: AgentConfiguration;
  metadata?: AgentMetadata;
}

export type AgentStatus = 'active' | 'inactive' | 'running' | 'stopped' | 'error' | 'paused';

export interface AgentConfiguration {
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  stopSequences?: string[];
  parameters?: Record<string, unknown>;
}

export interface AgentMetadata {
  totalRuns?: number;
  lastRun?: string;
  successRate?: number;
  averageDuration?: number;
}

// User Types
export interface User {
  id: string;
  username: string;
  email: string;
  displayName?: string;
  avatar?: string;
  role: UserRole;
  preferences?: UserPreferences;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'user' | 'guest' | 'collaborator';

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  language?: string;
  fontSize?: 'small' | 'medium' | 'large';
  animations?: boolean;
  highContrast?: boolean;
  reduceMotion?: boolean;
}

// Execution Types
export interface AgentExecution {
  id: string;
  agentId: string;
  input: string;
  output?: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  tokensUsed?: {
    input: number;
    output: number;
    total: number;
  };
  cost?: number;
  model?: string;
  error?: string;
}

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'error' | 'cancelled' | 'timeout';

// Template Types
export interface Template {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  configuration: AgentConfiguration;
  parameters?: TemplateParameter[];
  createdAt: string;
  updatedAt: string;
}

export interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  default?: unknown;
  required: boolean;
  description?: string;
  options?: unknown[];
}

// Pagination Types
export interface Pagination<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
  filter?: Record<string, unknown>;
}

// Filter Types
export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterGroup {
  id: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'date' | 'search';
  options?: FilterOption[];
  value?: unknown;
}

// Sort Types
export interface SortOption {
  value: string;
  label: string;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Theme Types (re-export from theme)
export type { Theme, ThemeConfig } from '../theme/types';

// Utility Types
export type Maybe<T> = T | null | undefined;
export type NonNullable<T> = Exclude<T, null | undefined>;
export type Nullable<T> = T | null;
export type ValueOf<T> = T[keyof T];
export type KeysOf<T> = keyof T;

// Event Types
export interface CustomEvent<T = unknown> {
  type: string;
  payload?: T;
  timestamp?: number;
}

// Modal Types
export interface ModalConfig {
  id: string;
  title: string;
  content: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showClose?: boolean;
  closeOnBackdrop?: boolean;
  actions?: React.ReactNode;
}

// Toast Types
export interface ToastMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  duration?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  dismissible?: boolean;
}

// Form Types
export interface FormError {
  field: string;
  message: string;
  type?: 'required' | 'validation' | 'server';
}

export interface FormState<T = unknown> {
  values: T;
  errors: FormError[];
  isSubmitting: boolean;
  isValid: boolean;
  touched: Record<string, boolean>;
}

// Query Types
export interface QueryParams {
  [key: string]: string | number | boolean | undefined;
}

// Storage Types
export interface StorageItem<T = unknown> {
  key: string;
  value: T;
  expiresAt?: number;
}

// Import/Export Types
export interface ImportData<T = unknown> {
  version: string;
  timestamp: string;
  data: T;
}

export interface ExportData<T = unknown> extends ImportData<T> {
  metadata?: {
    name?: string;
    description?: string;
    author?: string;
  };
}
