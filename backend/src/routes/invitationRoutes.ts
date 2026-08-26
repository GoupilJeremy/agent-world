/**
 * Agent World - Invitation Routes
 * Routes pour la gestion des invitations
 * Conforme aux exigences US-040 : Invitation d'utilisateurs
 */

import { Router } from 'express';
import {
  createInvitation,
  getProjectInvitations,
  getSentInvitations,
  getReceivedInvitations,
  acceptInvitation,
  rejectInvitation,
  cancelInvitation,
  resendInvitation,
  getInvitationByToken,
} from '../controllers/invitationController.js';
import { requirePermission, requireProjectAdmin } from '../middleware/rbacMiddleware.js';

const router = Router();

// ============================================================================
// Invitation Routes
// ============================================================================

/**
 * POST /api/invitations
 * Create a new invitation for a project
 * Requires: invite:create permission
 */
router.post('/', requirePermission('invite:create'), createInvitation);

/**
 * GET /api/projects/:projectId/invitations
 * Get all invitations for a specific project
 * Requires: invite:read permission
 */
router.get('/projects/:projectId', requirePermission('invite:read'), getProjectInvitations);

/**
 * GET /api/invitations/sent
 * Get all invitations sent by the current user
 * Requires: invite:read permission
 */
router.get('/sent', requirePermission('invite:read'), getSentInvitations);

/**
 * GET /api/invitations/received
 * Get all invitations received by the current user
 * No permission required (for invitation acceptance flow)
 */
router.get('/received', getReceivedInvitations);

/**
 * POST /api/invitations/:invitationId/accept
 * Accept an invitation
 * No permission required (for invitation acceptance flow)
 */
router.post('/:invitationId/accept', acceptInvitation);

/**
 * POST /api/invitations/:invitationId/reject
 * Reject an invitation
 * No permission required (for invitation flow)
 */
router.post('/:invitationId/reject', rejectInvitation);

/**
 * DELETE /api/invitations/:invitationId
 * Cancel an invitation (sender only)
 * Requires: invite:manage permission
 */
router.delete('/:invitationId', requirePermission('invite:manage'), cancelInvitation);

/**
 * POST /api/invitations/:invitationId/resend
 * Resend an invitation
 * Requires: invite:manage permission
 */
router.post('/:invitationId/resend', requirePermission('invite:manage'), resendInvitation);

/**
 * GET /api/invitations/token/:token
 * Get invitation by token (for accepting via link)
 * No authentication required
 */
router.get('/token/:token', getInvitationByToken);

// ============================================================================
// Bulk Operations
// ============================================================================

/**
 * POST /api/projects/:projectId/invitations/bulk
 * Create multiple invitations at once
 */
// router.post('/projects/:projectId/bulk', requirePermission('invite:create'), bulkCreateInvitations);

/**
 * DELETE /api/projects/:projectId/invitations
 * Cancel all pending invitations for a project
 */
// router.delete('/projects/:projectId', requirePermission('invite:manage'), cancelAllProjectInvitations);

// ============================================================================
// Admin Routes
// ============================================================================

/**
 * GET /api/admin/invitations
 * Get all invitations (admin only)
 * Requires: invite:manage permission at admin level
 */
// router.get('/admin', requireProjectAdmin, getAllInvitations);

export default router;
