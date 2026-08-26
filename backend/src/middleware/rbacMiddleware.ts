/**
 * Agent World - RBAC Middleware
 * Middleware for Role-Based Access Control
 * Conforme aux exigences US-041 : Gestion des rôles
 */

import { Request, Response, NextFunction } from 'express';
import { Permission, ALL_PERMISSIONS } from '../types/collaboration.js';

// Type for request with user attached
export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    permissions: Permission[];
    projectId?: string;
  };
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(userPermissions: Permission[], requiredPermission: Permission): boolean {
  return userPermissions.includes(requiredPermission);
}

/**
 * Check if user has all required permissions
 */
export function hasAllPermissions(userPermissions: Permission[], requiredPermissions: Permission[]): boolean {
  return requiredPermissions.every((permission) => userPermissions.includes(permission));
}

/**
 * Check if user has any of the required permissions
 */
export function hasAnyPermission(userPermissions: Permission[], requiredPermissions: Permission[]): boolean {
  return requiredPermissions.some((permission) => userPermissions.includes(permission));
}

/**
 * RBAC Middleware: Check if user has required permission
 * @param requiredPermission - Single permission to check
 */
export function requirePermission(requiredPermission: Permission) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!user.permissions) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'No permissions assigned',
      });
    }

    if (!hasPermission(user.permissions, requiredPermission)) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: `Permission '${requiredPermission}' required`,
        requiredPermission,
        userPermissions: user.permissions,
      });
    }

    next();
  };
}

/**
 * RBAC Middleware: Check if user has all required permissions
 * @param requiredPermissions - Array of permissions to check
 */
export function requireAllPermissions(requiredPermissions: Permission[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!user.permissions) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'No permissions assigned',
      });
    }

    const missingPermissions = requiredPermissions.filter(
      (permission) => !user.permissions.includes(permission)
    );

    if (missingPermissions.length > 0) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Missing required permissions',
        missingPermissions,
      });
    }

    next();
  };
}

/**
 * RBAC Middleware: Check if user has any of the required permissions
 * @param requiredPermissions - Array of permissions to check (any one required)
 */
export function requireAnyPermission(requiredPermissions: Permission[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required',
      });
    }

    if (!user.permissions || user.permissions.length === 0) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'No permissions assigned',
      });
    }

    if (!hasAnyPermission(user.permissions, requiredPermissions)) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: `Requires one of: ${requiredPermissions.join(', ')}`,
        requiredPermissions,
        userPermissions: user.permissions,
      });
    }

    next();
  };
}

/**
 * RBAC Middleware: Check if user is project admin
 */
export function requireProjectAdmin(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const user = req.user;

  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      message: 'Authentication required',
    });
  }

  // Admin has all permissions in their project
  const isAdmin = hasAllPermissions(user.permissions, [
    'member:manage',
    'role:manage',
    'invite:manage',
    'project:update',
    'project:delete',
  ]);

  if (!isAdmin) {
    return res.status(403).json({
      success: false,
      error: 'Forbidden',
      message: 'Project admin permissions required',
    });
  }

  next();
}

/**
 * RBAC Middleware: Check if user is project owner
 */
export function requireProjectOwner(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const user = req.user;

  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      message: 'Authentication required',
    });
  }

  // Owner has a special role that can't be modified
  // This would be checked against the database in a real implementation
  // For now, we check for a special permission
  const isOwner = hasPermission(user.permissions, 'project:delete');

  if (!isOwner) {
    return res.status(403).json({
      success: false,
      error: 'Forbidden',
      message: 'Project owner permissions required',
    });
  }

  next();
}

/**
 * Get user permissions from request
 */
export function getUserPermissions(req: AuthenticatedRequest): Permission[] {
  return req.user?.permissions || [];
}

/**
 * Validate permission string
 */
export function isValidPermission(permission: string): permission is Permission {
  return ALL_PERMISSIONS.includes(permission as Permission);
}

/**
 * Validate array of permissions
 */
export function validatePermissions(permissions: string[]): Permission[] {
  return permissions.filter(isValidPermission);
}

export default {
  requirePermission,
  requireAllPermissions,
  requireAnyPermission,
  requireProjectAdmin,
  requireProjectOwner,
  hasPermission,
  hasAllPermissions,
  hasAnyPermission,
  getUserPermissions,
  isValidPermission,
  validatePermissions,
};
