/**
 * Agent World - Invitation Controller
 * Contrôleur pour la gestion des invitations
 * Conforme aux exigences US-040 : Invitation d'utilisateurs
 */

import { Request, Response } from 'express';
import { nanoid } from 'nanoid';
import { Invitation, InvitationInput, InvitationStatus, ApiResponse, PaginatedResponse, PaginationParams } from '../types/collaboration.js';
import { requirePermission, AuthenticatedRequest } from '../middleware/rbacMiddleware.js';

// In-memory storage for now (will be replaced with database)
let invitations: Invitation[] = [];

// Token expiration: 72 hours by default
const DEFAULT_EXPIRATION_HOURS = 72;
const TOKEN_LENGTH = 32;

/**
 * Generate a unique invitation token
 */
function generateInvitationToken(): string {
  return nanoid(TOKEN_LENGTH);
}

/**
 * Get expiration date based on hours
 */
function getExpirationDate(hours: number): Date {
  const date = new Date();
  date.setHours(date.getHours() + hours);
  return date;
}

/**
 * Create a new invitation
 * POST /api/invitations
 */
export async function createInvitation(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    const { projectId, email, roleId, expiresIn = DEFAULT_EXPIRATION_HOURS }: InvitationInput = req.body;

    // Validate required fields
    if (!projectId || !email || !roleId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'projectId, email, and roleId are required',
      });
    }

    // Check if user has permission to invite
    // This would be replaced with actual permission check from database
    const hasInvitePermission = true; // Placeholder
    
    if (!hasInvitePermission) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'No permission to invite users',
      });
    }

    // Generate token and expiration
    const token = generateInvitationToken();
    const expiresAt = getExpirationDate(expiresIn);

    // Create invitation
    const invitation: Invitation = {
      id: nanoid(),
      projectId,
      fromUserId: user.id,
      toUserId: null, // Will be set when user registers/accepts
      email,
      roleId,
      token,
      status: 'pending',
      expiresAt,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Store invitation
    invitations.push(invitation);

    // TODO: Send email with invitation link
    // await emailService.sendInvitationEmail(email, invitation);

    return res.status(201).json({
      success: true,
      data: {
        invitation: {
          ...invitation,
          // Don't return token in response for security
          token: undefined,
        },
      },
      message: 'Invitation created successfully',
    });
  } catch (error) {
    console.error('Error creating invitation:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to create invitation',
    });
  }
}

/**
 * Get all invitations for a project
 * GET /api/projects/:projectId/invitations
 */
export async function getProjectInvitations(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    const { projectId } = req.params;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!projectId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'projectId is required',
      });
    }

    // Filter invitations by project
    const projectInvitations = invitations.filter(
      (invitation) => invitation.projectId === projectId
    );

    return res.status(200).json({
      success: true,
      data: projectInvitations,
    });
  } catch (error) {
    console.error('Error getting project invitations:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to get project invitations',
    });
  }
}

/**
 * Get invitations sent by current user
 * GET /api/invitations/sent
 */
export async function getSentInvitations(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    const sentInvitations = invitations.filter(
      (invitation) => invitation.fromUserId === user.id
    );

    return res.status(200).json({
      success: true,
      data: sentInvitations,
    });
  } catch (error) {
    console.error('Error getting sent invitations:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to get sent invitations',
    });
  }
}

/**
 * Get invitations received by current user
 * GET /api/invitations/received
 */
export async function getReceivedInvitations(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    // Filter by email (in real implementation, would also check toUserId)
    const receivedInvitations = invitations.filter(
      (invitation) => invitation.email === user.email && invitation.status === 'pending'
    );

    return res.status(200).json({
      success: true,
      data: receivedInvitations,
    });
  } catch (error) {
    console.error('Error getting received invitations:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to get received invitations',
    });
  }
}

/**
 * Accept an invitation
 * POST /api/invitations/:invitationId/accept
 */
export async function acceptInvitation(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    const { invitationId } = req.params;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!invitationId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'invitationId is required',
      });
    }

    // Find invitation
    const invitationIndex = invitations.findIndex((inv) => inv.id === invitationId);
    
    if (invitationIndex === -1) {
      return res.status(404).json({
        success: false,
        error: 'Not Found',
        message: 'Invitation not found',
      });
    }

    const invitation = invitations[invitationIndex];

    // Check if invitation is for this user
    if (invitation.email !== user.email) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'This invitation is not for you',
      });
    }

    // Check if already accepted
    if (invitation.status !== 'pending') {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: `Invitation already ${invitation.status}`,
      });
    }

    // Check if expired
    if (new Date() > invitation.expiresAt) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'Invitation has expired',
      });
    }

    // Update invitation
    invitations[invitationIndex] = {
      ...invitation,
      toUserId: user.id,
      status: 'accepted',
      acceptedAt: new Date(),
      updatedAt: new Date(),
    };

    // TODO: Add user to project members with the specified role
    // await projectService.addMember(invitation.projectId, user.id, invitation.roleId);

    return res.status(200).json({
      success: true,
      message: 'Invitation accepted successfully',
    });
  } catch (error) {
    console.error('Error accepting invitation:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to accept invitation',
    });
  }
}

/**
 * Reject an invitation
 * POST /api/invitations/:invitationId/reject
 */
export async function rejectInvitation(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    const { invitationId } = req.params;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!invitationId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'invitationId is required',
      });
    }

    // Find invitation
    const invitationIndex = invitations.findIndex((inv) => inv.id === invitationId);
    
    if (invitationIndex === -1) {
      return res.status(404).json({
        success: false,
        error: 'Not Found',
        message: 'Invitation not found',
      });
    }

    const invitation = invitations[invitationIndex];

    // Check if invitation is for this user
    if (invitation.email !== user.email) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'This invitation is not for you',
      });
    }

    // Check if already processed
    if (invitation.status !== 'pending') {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: `Invitation already ${invitation.status}`,
      });
    }

    // Update invitation
    invitations[invitationIndex] = {
      ...invitation,
      status: 'rejected',
      rejectedAt: new Date(),
      updatedAt: new Date(),
    };

    return res.status(200).json({
      success: true,
      message: 'Invitation rejected successfully',
    });
  } catch (error) {
    console.error('Error rejecting invitation:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to reject invitation',
    });
  }
}

/**
 * Cancel an invitation (sender only)
 * DELETE /api/invitations/:invitationId
 */
export async function cancelInvitation(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    const { invitationId } = req.params;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!invitationId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'invitationId is required',
      });
    }

    // Find invitation
    const invitationIndex = invitations.findIndex((inv) => inv.id === invitationId);
    
    if (invitationIndex === -1) {
      return res.status(404).json({
        success: false,
        error: 'Not Found',
        message: 'Invitation not found',
      });
    }

    const invitation = invitations[invitationIndex];

    // Check if user is the sender
    if (invitation.fromUserId !== user.id) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Only the invitation sender can cancel it',
      });
    }

    // Check if already processed
    if (invitation.status !== 'pending') {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: `Invitation already ${invitation.status}`,
      });
    }

    // Update invitation
    invitations[invitationIndex] = {
      ...invitation,
      status: 'cancelled',
      cancelledAt: new Date(),
      updatedAt: new Date(),
    };

    return res.status(200).json({
      success: true,
      message: 'Invitation cancelled successfully',
    });
  } catch (error) {
    console.error('Error cancelling invitation:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to cancel invitation',
    });
  }
}

/**
 * Resend an invitation
 * POST /api/invitations/:invitationId/resend
 */
export async function resendInvitation(req: AuthenticatedRequest, res: Response) {
  try {
    const user = req.user;
    const { invitationId } = req.params;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!invitationId) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'invitationId is required',
      });
    }

    // Find invitation
    const invitationIndex = invitations.findIndex((inv) => inv.id === invitationId);
    
    if (invitationIndex === -1) {
      return res.status(404).json({
        success: false,
        error: 'Not Found',
        message: 'Invitation not found',
      });
    }

    const invitation = invitations[invitationIndex];

    // Check if user is the sender
    if (invitation.fromUserId !== user.id) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Only the invitation sender can resend it',
      });
    }

    // Check if already accepted
    if (invitation.status === 'accepted') {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'Cannot resend an accepted invitation',
      });
    }

    // Generate new token and extend expiration
    const newToken = generateInvitationToken();
    const newExpiresAt = getExpirationDate(DEFAULT_EXPIRATION_HOURS);

    // Update invitation
    invitations[invitationIndex] = {
      ...invitation,
      token: newToken,
      expiresAt: newExpiresAt,
      status: 'pending',
      updatedAt: new Date(),
    };

    // TODO: Resend email
    // await emailService.sendInvitationEmail(invitation.email, invitations[invitationIndex]);

    return res.status(200).json({
      success: true,
      message: 'Invitation resent successfully',
    });
  } catch (error) {
    console.error('Error resending invitation:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to resend invitation',
    });
  }
}

/**
 * Get invitation by token (for accepting via link)
 * GET /api/invitations/token/:token
 */
export async function getInvitationByToken(req: Request, res: Response) {
  try {
    const { token } = req.params;

    if (!token) {
      return res.status(400).json({
        success: false,
        error: 'Bad Request',
        message: 'Token is required',
      });
    }

    // Find invitation by token
    const invitation = invitations.find((inv) => inv.token === token);

    if (!invitation) {
      return res.status(404).json({
        success: false,
        error: 'Not Found',
        message: 'Invitation not found',
      });
    }

    // Don't expose sensitive info
    const publicInvitation = {
      id: invitation.id,
      projectId: invitation.projectId,
      email: invitation.email,
      roleId: invitation.roleId,
      status: invitation.status,
      expiresAt: invitation.expiresAt,
      createdAt: invitation.createdAt,
    };

    return res.status(200).json({
      success: true,
      data: publicInvitation,
    });
  } catch (error) {
    console.error('Error getting invitation by token:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Failed to get invitation',
    });
  }
}

export default {
  createInvitation,
  getProjectInvitations,
  getSentInvitations,
  getReceivedInvitations,
  acceptInvitation,
  rejectInvitation,
  cancelInvitation,
  resendInvitation,
  getInvitationByToken,
};
