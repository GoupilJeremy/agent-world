/**
 * Agent World - Collaboration Types
 * Types for EPIC 6: Collaboration features
 */

// ============================================================================
// Permission Types
// ============================================================================

export type Permission = 
  | 'agent:create'
  | 'agent:read'
  | 'agent:update'
  | 'agent:delete'
  | 'agent:execute'
  | 'project:read'
  | 'project:update'
  | 'project:delete'
  | 'project:create'
  | 'invite:create'
  | 'invite:manage'
  | 'invite:read'
  | 'role:create'
  | 'role:read'
  | 'role:update'
  | 'role:delete'
  | 'role:manage'
  | 'member:create'
  | 'member:read'
  | 'member:update'
  | 'member:delete'
  | 'member:manage'
  | 'comment:create'
  | 'comment:read'
  | 'comment:update'
  | 'comment:delete'
  | 'conflict:read'
  | 'conflict:resolve'
  | 'chat:read'
  | 'chat:create'
  | 'chat:update'
  | 'chat:delete';

// Permission categories for easier management
export const AGENT_PERMISSIONS: Permission[] = [
  'agent:create',
  'agent:read',
  'agent:update',
  'agent:delete',
  'agent:execute',
];

export const PROJECT_PERMISSIONS: Permission[] = [
  'project:read',
  'project:update',
  'project:delete',
  'project:create',
];

export const INVITATION_PERMISSIONS: Permission[] = [
  'invite:create',
  'invite:manage',
  'invite:read',
];

export const ROLE_PERMISSIONS: Permission[] = [
  'role:create',
  'role:read',
  'role:update',
  'role:delete',
  'role:manage',
];

export const MEMBER_PERMISSIONS: Permission[] = [
  'member:create',
  'member:read',
  'member:update',
  'member:delete',
  'member:manage',
];

export const COMMENT_PERMISSIONS: Permission[] = [
  'comment:create',
  'comment:read',
  'comment:update',
  'comment:delete',
];

export const CONFLICT_PERMISSIONS: Permission[] = [
  'conflict:read',
  'conflict:resolve',
];

export const CHAT_PERMISSIONS: Permission[] = [
  'chat:read',
  'chat:create',
  'chat:update',
  'chat:delete',
];

export const ALL_PERMISSIONS: Permission[] = [
  ...AGENT_PERMISSIONS,
  ...PROJECT_PERMISSIONS,
  ...INVITATION_PERMISSIONS,
  ...ROLE_PERMISSIONS,
  ...MEMBER_PERMISSIONS,
  ...COMMENT_PERMISSIONS,
  ...CONFLICT_PERMISSIONS,
  ...CHAT_PERMISSIONS,
];

// ============================================================================
// Invitation Types
// ============================================================================

export type InvitationStatus = 'pending' | 'accepted' | 'rejected' | 'expired' | 'cancelled';

export interface Invitation {
  id: string;
  projectId: string;
  fromUserId: string;
  toUserId: string | null;
  email: string;
  roleId: string;
  token: string;
  status: InvitationStatus;
  expiresAt: Date;
  acceptedAt?: Date;
  rejectedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface InvitationInput {
  projectId: string;
  email: string;
  roleId: string;
  expiresIn?: number; // hours until expiration (default: 72)
}

export interface InvitationWithUser extends Invitation {
  fromUser?: {
    id: string;
    email: string;
    name: string;
  };
  toUser?: {
    id: string;
    email: string;
    name: string;
  };
  role?: Role;
  project?: {
    id: string;
    name: string;
  };
}

// ============================================================================
// Role Types
// ============================================================================

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  isDefault: boolean;
  isSystem: boolean; // Cannot be modified or deleted
  projectId: string | null; // null for global roles
  createdAt: Date;
  updatedAt: Date;
}

export interface RoleInput {
  name: string;
  description?: string;
  permissions: Permission[];
  projectId?: string | null;
}

// Predefined role names
export type PredefinedRoleName = 'owner' | 'admin' | 'editor' | 'viewer' | 'guest';

// ============================================================================
// Project Member Types
// ============================================================================

export interface ProjectMember {
  id: string;
  projectId: string;
  userId: string;
  roleId: string;
  joinedAt: Date;
  lastActiveAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectMemberWithDetails extends ProjectMember {
  user: {
    id: string;
    email: string;
    name: string;
    avatar?: string;
  };
  role: Role;
}

// ============================================================================
// Comment Types
// ============================================================================

export interface Comment {
  id: string;
  agentId: string;
  projectId: string;
  userId: string;
  content: string;
  parentId: string | null; // For threaded comments
  mentions: string[]; // Array of mentioned user IDs
  isEdited: boolean;
  editedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface CommentInput {
  agentId: string;
  content: string;
  parentId?: string | null;
}

export interface CommentWithUser extends Comment {
  user: {
    id: string;
    email: string;
    name: string;
    avatar?: string;
  };
  replies?: CommentWithUser[];
}

// ============================================================================
// Audit Log Types
// ============================================================================

export type AuditEntityType = 'agent' | 'project' | 'template' | 'comment' | 'invitation' | 'role' | 'member';

export type AuditAction = 'create' | 'read' | 'update' | 'delete' | 'execute' | 'share' | 'invite' | 'join' | 'leave';

export interface AuditLog {
  id: string;
  projectId: string;
  userId: string;
  action: AuditAction;
  entityType: AuditEntityType;
  entityId: string;
  oldValue?: Record<string, unknown>;
  newValue?: Record<string, unknown>;
  changes?: Record<string, { old: unknown; new: unknown }>;
  timestamp: Date;
  ipAddress?: string;
  userAgent?: string;
}

export interface AuditLogFilter {
  projectId?: string;
  userId?: string;
  entityType?: AuditEntityType;
  entityId?: string;
  action?: AuditAction;
  startDate?: Date;
  endDate?: Date;
}

// ============================================================================
// Conflict Types
// ============================================================================

export type ConflictStatus = 'open' | 'resolved' | 'merged' | 'dismissed';

export interface Conflict {
  id: string;
  agentId: string;
  projectId: string;
  field: string; // Which field has the conflict
  baseVersion: string; // Base version hash or ID
  theirVersion: string; // Their version hash or ID
  myVersion: string; // Current user's version hash or ID
  theirValue: Record<string, unknown>;
  myValue: Record<string, unknown>;
  userIds: string[]; // All users involved in the conflict
  status: ConflictStatus;
  resolvedBy?: string;
  resolvedAt?: Date;
  resolution?: string; // How it was resolved
  createdAt: Date;
  updatedAt: Date;
}

export interface ConflictResolution {
  conflictId: string;
  resolution: 'use_mine' | 'use_theirs' | 'merge' | 'custom';
  resolvedValue?: Record<string, unknown>;
  resolutionNote?: string;
}

// ============================================================================
// Chat Types
// ============================================================================

export interface ChatMessage {
  id: string;
  projectId: string;
  userId: string;
  content: string;
  attachments: string[]; // Array of file URLs
  reactions: Record<string, string[]>; // emoji -> user IDs
  readBy: string[]; // User IDs who have read the message
  isEdited: boolean;
  editedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessageInput {
  projectId: string;
  content: string;
  attachments?: string[];
}

export interface ChatMessageWithUser extends ChatMessage {
  user: {
    id: string;
    email: string;
    name: string;
    avatar?: string;
    isOnline?: boolean;
  };
}

// WebSocket events
export interface ChatEvent {
  type: 'message' | 'typing' | 'read' | 'reaction' | 'delete' | 'edit';
  data: unknown;
}

export interface MessageEvent extends ChatEvent {
  type: 'message';
  data: ChatMessageWithUser;
}

export interface TypingEvent extends ChatEvent {
  type: 'typing';
  data: {
    userId: string;
    projectId: string;
    isTyping: boolean;
  };
}

export interface ReadEvent extends ChatEvent {
  type: 'read';
  data: {
    userId: string;
    projectId: string;
    messageIds: string[];
  };
}

export interface ReactionEvent extends ChatEvent {
  type: 'reaction';
  data: {
    messageId: string;
    emoji: string;
    added: boolean; // true = add, false = remove
    userId: string;
  };
}

export interface DeleteEvent extends ChatEvent {
  type: 'delete';
  data: {
    messageId: string;
    deletedBy: string;
  };
}

export interface EditEvent extends ChatEvent {
  type: 'edit';
  data: {
    messageId: string;
    newContent: string;
    editedBy: string;
  };
}

// ============================================================================
// Project Types (Extended for Collaboration)
// ============================================================================

export interface ProjectVisibility {
  isPublic: boolean;
  shareToken?: string;
  shareTokenExpiresAt?: Date;
  allowPublicInvites: boolean;
}

export interface ProjectSharingSettings {
  visibility: 'private' | 'project_members' | 'organization' | 'public';
  inviteLinkEnabled: boolean;
  inviteLinkExpiresIn?: number; // hours
}

// ============================================================================
// Response Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// ============================================================================
// Utility Types
// ============================================================================

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<
  T,
  Exclude<keyof T, Keys>
> &
  {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

export type RequireAllOrNone<T> = T | Partial<Record<keyof T, never>>;
