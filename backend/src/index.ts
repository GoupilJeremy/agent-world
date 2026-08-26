/**
 * Agent World - Backend Server Entry Point
 * Point d'entrée principal du serveur backend
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const PORT = process.env.PORT || 3001;
const NODE_ENV = process.env.NODE_ENV || 'development';

// ============================================================================
// Express App Setup
// ============================================================================

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true,
  },
});

// Security middleware
app.use(helmet());

// CORS configuration
app.use(
  cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true,
  })
);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ============================================================================
// Request Logging
// ============================================================================

app.use((req, res, next) => {
  if (NODE_ENV === 'development') {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  }
  next();
});

// ============================================================================
// Health Check
// ============================================================================

app.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '0.4.0',
    service: 'agent-world-backend',
  });
});

app.get('/api/health', (req, res) => {
  res.status(200).json({
    success: true,
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '0.4.0',
  });
});

// ============================================================================
// API Routes
// ============================================================================

// Import and mount routes
import invitationRoutes from './routes/invitationRoutes.js';

// Mount invitation routes
app.use('/api/invitations', invitationRoutes);

// ============================================================================
// WebSocket / Socket.io Setup
// ============================================================================

// Track connected users
const connectedUsers = new Map<string, string>(); // userId -> socketId

io.on('connection', (socket) => {
  console.log(`[Socket.IO] New connection: ${socket.id}`);

  // Handle authentication
  socket.on('authenticate', (userId: string) => {
    connectedUsers.set(userId, socket.id);
    console.log(`[Socket.IO] User authenticated: ${userId}`);
    socket.join(userId);
  });

  // Handle joining a project room
  socket.on('joinProject', (projectId: string) => {
    socket.join(projectId);
    console.log(`[Socket.IO] Socket ${socket.id} joined project: ${projectId}`);
  });

  // Handle leaving a project room
  socket.on('leaveProject', (projectId: string) => {
    socket.leave(projectId);
    console.log(`[Socket.IO] Socket ${socket.id} left project: ${projectId}`);
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    // Remove from connected users
    for (const [userId, socketId] of connectedUsers.entries()) {
      if (socketId === socket.id) {
        connectedUsers.delete(userId);
        console.log(`[Socket.IO] User disconnected: ${userId}`);
        break;
      }
    }
    console.log(`[Socket.IO] Disconnected: ${socket.id}`);
  });
});

// Export io for use in other modules
export { io, connectedUsers };

// ============================================================================
// Error Handling
// ============================================================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Not Found',
    message: 'Route not found',
  });
});

// Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('[Error]:', err);
  res.status(500).json({
    success: false,
    error: 'Internal Server Error',
    message: NODE_ENV === 'development' ? err.message : 'Something went wrong',
    stack: NODE_ENV === 'development' ? err.stack : undefined,
  });
});

// ============================================================================
// Start Server
// ============================================================================

httpServer.listen(PORT, () => {
  console.log(`
  ╔══════════════════════════════════════════════════════════╗
  ║          🤖 Agent World Backend Server                   ║
  ╠══════════════════════════════════════════════════════════╣
  ║  📋 Version:    0.4.0 (EPIC 6 - Collaboration)           ║
  ║  🏠 Local:      http://localhost:${PORT}                  ║
  ║  🌍 Environment: ${NODE_ENV}                                  ║
  ║  📡 Socket.IO:  Connected                                 ║
  ╚══════════════════════════════════════════════════════════╝
  `);
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('\n[Signal] SIGTERM received. Shutting down gracefully...');
  httpServer.close(() => {
    console.log('[Server] Closed.');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n[Signal] SIGINT received. Shutting down gracefully...');
  httpServer.close(() => {
    console.log('[Server] Closed.');
    process.exit(0);
  });
});

export default app;
