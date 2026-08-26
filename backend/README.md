# Agent World Backend

Backend API for Agent World - AI Agent Management Platform

## 📋 Overview

This is the backend server for Agent World, implementing the collaboration features (EPIC 6) including:

- **User Invitations** (US-040)
- **Role Management** (US-041)
- **Project Sharing** (US-042)
- **Agent Comments** (US-043)
- **Modification History** (US-044)
- **Conflict Resolution** (US-045)
- **Real-time Chat** (US-046)

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0 or yarn >= 1.22.0
- SQLite (for development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/GoupilJeremy/agent-world.git
   cd agent-world/backend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Generate Prisma client:
   ```bash
   npm run db:generate
   ```

4. Set up database:
   ```bash
   npm run db:push
   # or for migrations:
   npm run db:migrate
   ```

5. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

6. Start development server:
   ```bash
   npm run dev
   ```

7. For production:
   ```bash
   npm run build
   npm start
   ```

## 🌍 Environment Variables

Create a `.env` file in the backend directory:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Database
DATABASE_URL="file:./dev.db"

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Email Configuration (for invitations)
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=your-email@example.com
# SMTP_PASS=your-email-password
# EMAIL_FROM=invitations@agent-world.com

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

## 🏗️ Project Structure

```
backend/
├── src/
│   ├── index.ts                      # Server entry point
│   ├── types/
│   │   └── collaboration.ts          # Collaboration TypeScript types
│   ├── controllers/
│   │   └── invitationController.ts   # Invitation controller
│   ├── middleware/
│   │   └── rbacMiddleware.ts         # Role-Based Access Control
│   ├── routes/
│   │   └── invitationRoutes.ts       # Invitation routes
│   └── services/                     # Business logic services
├── prisma/
│   ├── schema.prisma                 # Prisma schema
│   └── migrations/                   # Database migrations
├── config/
│   └── permissions.ts                # Permission configuration
├── package.json
├── tsconfig.json
└── README.md
```

## 🎯 API Endpoints

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/api/health` | API health check |

### Invitations (US-040)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/api/invitations` | Create invitation | `invite:create` |
| GET | `/api/projects/:projectId/invitations` | Get project invitations | `invite:read` |
| GET | `/api/invitations/sent` | Get sent invitations | `invite:read` |
| GET | `/api/invitations/received` | Get received invitations | - |
| POST | `/api/invitations/:id/accept` | Accept invitation | - |
| POST | `/api/invitations/:id/reject` | Reject invitation | - |
| DELETE | `/api/invitations/:id` | Cancel invitation | `invite:manage` |
| POST | `/api/invitations/:id/resend` | Resend invitation | `invite:manage` |
| GET | `/api/invitations/token/:token` | Get by token | - |

### Roles (US-041)

*Coming soon...*

### Comments (US-043)

*Coming soon...*

### Chat (US-046)

*Coming soon...*

## 🔐 RBAC (Role-Based Access Control)

The backend implements a comprehensive RBAC system with the following permissions:

### Permission Categories

- **Agent**: `agent:create`, `agent:read`, `agent:update`, `agent:delete`, `agent:execute`
- **Project**: `project:create`, `project:read`, `project:update`, `project:delete`
- **Invitation**: `invite:create`, `invite:read`, `invite:manage`
- **Role**: `role:create`, `role:read`, `role:update`, `role:delete`, `role:manage`
- **Member**: `member:create`, `member:read`, `member:update`, `member:delete`, `member:manage`
- **Comment**: `comment:create`, `comment:read`, `comment:update`, `comment:delete`
- **Conflict**: `conflict:read`, `conflict:resolve`
- **Chat**: `chat:create`, `chat:read`, `chat:update`, `chat:delete`

### Predefined Roles

| Role | Permissions |
|------|-------------|
| **Owner** | All permissions |
| **Admin** | All except project deletion |
| **Editor** | Create, read, update agents and comments |
| **Viewer** | Read-only access |
| **Guest** | Limited read access |

### Middleware

Use the RBAC middleware in your routes:

```typescript
import { requirePermission, requireProjectAdmin } from './middleware/rbacMiddleware.js';

// Single permission
router.get('/protected', requirePermission('agent:read'), controller);

// Multiple permissions (all required)
router.post('/admin', requireAllPermissions(['member:manage', 'role:manage']), controller);

// Any of the permissions
router.get('/data', requireAnyPermission(['agent:read', 'project:read']), controller);

// Project admin check
router.delete('/project', requireProjectAdmin, controller);
```

## 💬 WebSocket / Socket.IO

The backend includes Socket.IO for real-time features like chat.

### Events

**Connection:**
- `connect` - New connection established
- `disconnect` - Connection closed

**Authentication:**
- `authenticate` (userId: string) - Authenticate user with socket

**Project Rooms:**
- `joinProject` (projectId: string) - Join a project room
- `leaveProject` (projectId: string) - Leave a project room

**Chat Events:**
- `message` - New chat message
- `typing` - User is typing
- `read` - Message read receipt
- `reaction` - Emoji reaction

## 🗄️ Database

The project uses Prisma ORM with SQLite (default for development).

### Models

- **User** - User accounts
- **Project** - Projects containing agents
- **Agent** - AI agents
- **Template** - Agent templates
- **Invitation** - User invitations
- **Role** - User roles
- **ProjectMember** - Project member assignments
- **Comment** - Agent comments
- **AuditLog** - Modification history
- **Conflict** - Conflict detection
- **ChatMessage** - Chat messages
- **UserPresence** - Online status

### Migrations

```bash
# Create new migration
npm run db:migrate

# Push schema changes (development)
npm run db:push

# Generate Prisma client
npm run db:generate

# Open Prisma Studio (GUI)
npm run db:studio
```

## 📊 Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build TypeScript to JavaScript |
| `npm start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Run ESLint and fix issues |
| `npm test` | Run tests |
| `npm run db:generate` | Generate Prisma client |
| `npm run db:migrate` | Run database migrations |
| `npm run db:push` | Push schema to database |
| `npm run db:studio` | Open Prisma Studio |

## 🎨 Architecture

### Express + TypeScript

- **Express 4** - Web framework
- **TypeScript** - Type-safe JavaScript
- **ES Modules** - Modern module system
- **Zod** - Schema validation

### Real-time

- **Socket.IO** - WebSocket implementation
- **Room-based** - Organize connections by project

### Security

- **Helmet** - HTTP security headers
- **CORS** - Cross-origin resource sharing
- **Rate Limiting** - Prevent abuse
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

### Database

- **Prisma** - ORM
- **SQLite** - Default development database
- **PostgreSQL/MySQL** - Production options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run lint: `npm run lint`
5. Run tests: `npm test`
6. Commit your changes
7. Push to the branch
8. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](../../LICENSE) file for details.

## 🔗 Links

- [Frontend](../../frontend/README.md)
- [Documentation](../../docs)
- [Backlog](../../BACKLOG.md)
