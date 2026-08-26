# Agent World - EPIC 6 Collaboration Implementation Plan

**Version**: 1.0.0  
**Date**: 26 août 2026  
**Target Version**: v0.4.0  
**Due Date**: 30 septembre 2026

---

## 🎯 Overview

This document outlines the implementation plan for **EPIC 6: Collaboration**, which adds team collaboration features to Agent World. This epic enables users to work together on projects, share agents, and communicate effectively.

---

## 📋 User Stories

### 🔹 US-040: User Invitations
**Priority**: P2 (Could Have)  
**Estimated Hours**: 5h  
**Status**: ⏳ To Do

**Description**: Allow users to invite other people to join a project.

**Acceptance Criteria**:
- [ ] Email-based invitation system
- [ ] Invitation tokens with expiration
- [ ] Role assignment on invitation (admin/member)
- [ ] Invitation status tracking (pending/accepted/rejected)
- [ ] Resend invitation capability
- [ ] API endpoints for invitations

**Technical Implementation**:
- Backend: Invitation model, email service integration, token generation
- Frontend: Invitation UI in project settings
- API: `/api/invitations` (CRUD operations)

---

### 🔹 US-041: Role Management
**Priority**: P2 (Could Have)  
**Estimated Hours**: 6h  
**Status**: ⏳ To Do

**Description**: Define roles with specific permissions (read-only, edit, admin).

**Acceptance Criteria**:
- [ ] 3+ predefined roles (viewer, editor, admin)
- [ ] Custom role creation
- [ ] Permission matrix (what each role can do)
- [ ] Role assignment/reassignment
- [ ] Role-based access control (RBAC) enforcement

**Technical Implementation**:
- Backend: Role model, Permission enum, RBAC middleware
- Frontend: Role management UI
- API: `/api/roles`, `/api/permissions`

**Roles & Permissions**:
| Role | Create Agent | Edit Agent | Delete Agent | Invite Users | Manage Roles | View Project |
|------|--------------|------------|--------------|--------------|--------------|---------------|
| Viewer | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Editor | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

### 🔹 US-042: Project Sharing
**Priority**: P2 (Could Have)  
**Estimated Hours**: 4h  
**Status**: ⏳ Backlog

**Description**: Share an entire project with a team or individual user.

**Acceptance Criteria**:
- [ ] Share project via link or email
- [ ] Access control settings per project
- [ ] Public/private project visibility
- [ ] Shareable link generation
- [ ] Permission inheritance from roles

**Technical Implementation**:
- Backend: Shareable link generation, access token validation
- Frontend: Share project modal/dialog
- API: `/api/projects/:id/share`

---

### 🔹 US-043: Agent Comments
**Priority**: P2 (Could Have)  
**Estimated Hours**: 5h  
**Status**: ⏳ Backlog

**Description**: Allow users to add comments on agents.

**Acceptance Criteria**:
- [ ] Comment system for agents
- [ ] Threaded/flat comment structure
- [ ] Mention other users (@username)
- [ ] Notifications for mentions
- [ ] Comment edit/delete
- [ ] Markdown support in comments

**Technical Implementation**:
- Backend: Comment model with agent reference, mention parsing
- Frontend: Comment component, mention autocomplete
- API: `/api/agents/:id/comments`

---

### 🔹 US-044: Modification History
**Priority**: P2 (Could Have)  
**Estimated Hours**: 6h  
**Status**: ⏳ Backlog

**Description**: Display the history of modifications made by each user.

**Acceptance Criteria**:
- [ ] Track all modifications with user attribution
- [ ] Filter by user
- [ ] View changes per agent/project
- [ ] Diff view for changes
- [ ] Timeline view

**Technical Implementation**:
- Backend: Audit log model, change tracking middleware
- Frontend: History viewer component
- API: `/api/audit-logs`

---

### 🔹 US-045: Conflict Resolution
**Priority**: P2 (Could Have)  
**Estimated Hours**: 8h  
**Status**: ⏳ Backlog

**Description**: Detect and resolve conflicts in modifications between users.

**Acceptance Criteria**:
- [ ] Conflict detection when multiple users edit same agent
- [ ] Visual conflict indicator
- [ ] Conflict resolution interface
- [ ] Merge changes manually
- [ ] Auto-merge for non-conflicting changes
- [ ] Conflict resolution history

**Technical Implementation**:
- Backend: Conflict detection algorithm, version comparison
- Frontend: Conflict resolution UI with diff view
- API: `/api/conflicts`, `/api/conflicts/:id/resolve`

---

### 🔹 US-046: Real-time Chat
**Priority**: P2 (Could Have)  
**Estimated Hours**: 6h  
**Status**: ⏳ Backlog

**Description**: Add an integrated chat for real-time team communication.

**Acceptance Criteria**:
- [ ] Chat per project
- [ ] Message history
- [ ] User presence indicators (online/offline)
- [ ] Message read receipts
- [ ] File/document sharing in chat
- [ ] Emoji reactions

**Technical Implementation**:
- Backend: WebSocket integration, message model
- Frontend: Chat component with real-time updates
- API: WebSocket endpoints, `/api/chat/messages`

---

## 🏗️ Technical Architecture

### Backend Structure
```
backend/
├── src/
│   ├── models/
│   │   ├── Invitation.ts
│   │   ├── Role.ts
│   │   ├── Permission.ts
│   │   ├── Comment.ts
│   │   ├── AuditLog.ts
│   │   ├── Conflict.ts
│   │   └── ChatMessage.ts
│   ├── controllers/
│   │   ├── invitationController.ts
│   │   ├── roleController.ts
│   │   ├── commentController.ts
│   │   ├── conflictController.ts
│   │   └── chatController.ts
│   ├── middleware/
│   │   └── rbacMiddleware.ts
│   ├── services/
│   │   ├── emailService.ts
│   │   ├── conflictDetectionService.ts
│   │   └── chatService.ts
│   └── routes/
│       ├── invitationRoutes.ts
│       ├── roleRoutes.ts
│       ├── commentRoutes.ts
│       ├── conflictRoutes.ts
│       └── chatRoutes.ts
└── config/
    └── permissions.ts
```

### Frontend Structure
```
frontend/src/
├── components/
│   ├── Collaboration/
│   │   ├── InvitationForm/
│   │   ├── RoleManager/
│   │   ├── ShareProjectModal/
│   │   ├── CommentSection/
│   │   ├── ConflictResolver/
│   │   └── Chat/
│   └── Common/
│       └── UserAvatar/
├── pages/
│   ├── ProjectSettings.tsx
│   ├── ProjectMembers.tsx
│   └── ProjectChat.tsx
├── hooks/
│   ├── useInvitations.ts
│   ├── useRoles.ts
│   ├── useComments.ts
│   ├── useChat.ts
│   └── useConflictResolution.ts
└── types/
    └── collaboration.ts
```

### Database Schema
```typescript
// User extensions
interface User {
  id: string;
  email: string;
  name: string;
  // ... existing fields
}

// Project extensions
interface Project {
  id: string;
  name: string;
  ownerId: string;
  isPublic: boolean;
  shareToken?: string;
  // ... existing fields
}

// New models
interface Invitation {
  id: string;
  projectId: string;
  fromUserId: string;
  toUserId: string;
  email: string;
  roleId: string;
  token: string;
  status: 'pending' | 'accepted' | 'rejected' | 'expired';
  expiresAt: Date;
  createdAt: Date;
  updatedAt: Date;
}

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  isDefault: boolean;
  projectId?: string; // null for global roles
}

type Permission = 
  | 'agent:create'
  | 'agent:read'
  | 'agent:update'
  | 'agent:delete'
  | 'project:read'
  | 'project:update'
  | 'project:delete'
  | 'invite:create'
  | 'invite:manage'
  | 'role:manage'
  | 'member:manage';

interface Comment {
  id: string;
  agentId: string;
  projectId: string;
  userId: string;
  content: string;
  parentId?: string; // for threaded comments
  mentions: string[]; // user IDs mentioned
  isEdited: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface AuditLog {
  id: string;
  projectId: string;
  userId: string;
  action: string;
  entityType: 'agent' | 'project' | 'template' | 'comment';
  entityId: string;
  oldValue?: any;
  newValue?: any;
  timestamp: Date;
  ipAddress?: string;
}

interface Conflict {
  id: string;
  agentId: string;
  projectId: string;
  userIds: string[]; // users involved in conflict
  field: string; // which field has conflict
  baseValue: any;
  theirValue: any;
  myValue: any;
  status: 'open' | 'resolved' | 'merged';
  resolvedBy?: string;
  resolvedAt?: Date;
  createdAt: Date;
}

interface ChatMessage {
  id: string;
  projectId: string;
  userId: string;
  content: string;
  attachments: string[]; // file URLs
  reactions: Record<string, string[]>; // emoji -> user IDs
  readBy: string[]; // user IDs who read the message
  isEdited: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

---

## 🎯 Implementation Timeline

### Sprint 5 (27 août - 9 septembre 2026)
**Objective**: Implement core collaboration foundation
- [ ] US-040: User Invitations (5h)
- [ ] US-041: Role Management (6h)
- [ ] Setup backend models and API endpoints
- [ ] Basic frontend components

**Deliverables**:
- Invitation system working
- Basic RBAC in place
- Project sharing foundation

---

### Sprint 6 (10 septembre - 23 septembre 2026)
**Objective**: Add communication and history features
- [ ] US-042: Project Sharing (4h)
- [ ] US-043: Agent Comments (5h)
- [ ] US-044: Modification History (6h)

**Deliverables**:
- Full project sharing
- Comment system functional
- Audit log system

---

### Sprint 7 (24 septembre - 7 octobre 2026)
**Objective**: Add conflict resolution and real-time chat
- [ ] US-045: Conflict Resolution (8h)
- [ ] US-046: Real-time Chat (6h)
- [ ] Integration testing
- [ ] Documentation

**Deliverables**:
- Conflict detection and resolution
- Real-time chat working
- All collaboration features integrated

---

## 🛠️ Dependencies

### External Services
- **Email Service**: For sending invitations (Nodemailer, SendGrid, or similar)
- **WebSocket**: For real-time chat (Socket.io or native WebSocket)

### Internal Dependencies
- EPIC 1: MVP (user authentication system)
- EPIC 4: History system (for modification tracking)
- EPIC 7: Notifications (for mention notifications)

---

## 📊 Success Metrics

1. **Invitation Success Rate**: >95% of invitations delivered successfully
2. **Permission Accuracy**: 100% of permission checks pass
3. **Conflict Detection**: All actual conflicts detected
4. **Chat Latency**: < 500ms for message delivery
5. **Comment Performance**: Load 100 comments in < 2 seconds

---

## 📝 Notes

1. **Security Considerations**:
   - All invitation tokens must expire
   - RBAC must be enforced at both API and UI levels
   - Chat messages should be encrypted at rest
   - Audit logs should be immutable

2. **Scalability Considerations**:
   - WebSocket connections need horizontal scaling
   - Comment pagination for large projects
   - Caching for permission checks

3. **UX Considerations**:
   - Real-time updates without page refresh
   - Clear visual indicators for conflicts
   - Easy role management interface

---

*Document generated on 26 août 2026*
