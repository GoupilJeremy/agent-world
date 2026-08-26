/**
 * Agent World - Alert Component
 * Composant alerte réutilisable du Design System
 * Conforme aux exigences US-060 : Design System
 */

import { forwardRef, HTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { AlertVariant } from '../../../theme/types';
import { X, Info, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

// Define alert props
export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  onClose?: () => void;
  closable?: boolean;
  icon?: ReactNode;
}

// Alert component with forwardRef
const Alert = forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      children,
      variant = 'info',
      title,
      onClose,
      closable = true,
      icon,
      className,
      ...props
    },
    ref
  ) => {
    // Base alert classes
    const baseClasses = `
      flex items-start gap-3
      p-4
      rounded-lg
      border
      animate-fade-in
      gpu-accelerate
    `;

    // Variant classes
    const variantClasses = {
      info: `
        bg-info-50
        border-info-200
        text-info-800
      `,
      success: `
        bg-success-50
        border-success-200
        text-success-800
      `,
      warning: `
        bg-warning-50
        border-warning-200
        text-warning-800
      `,
      error: `
        bg-error-50
        border-error-200
        text-error-800
      `,
    };

    // Icon component
    const getDefaultIcon = () => {
      switch (variant) {
        case 'info':
          return <Info className="w-5 h-5 flex-shrink-0" />;
        case 'success':
          return <CheckCircle className="w-5 h-5 flex-shrink-0" />;
        case 'warning':
          return <AlertTriangle className="w-5 h-5 flex-shrink-0" />;
        case 'error':
          return <XCircle className="w-5 h-5 flex-shrink-0" />;
        default:
          return <Info className="w-5 h-5 flex-shrink-0" />;
      }
    };

    // Merge all classes
    const alertClasses = twMerge(
      clsx(
        baseClasses,
        variantClasses[variant],
        className
      )
    );

    return (
      <div
        ref={ref}
        className={alertClasses}
        role="alert"
        aria-live="polite"
        {...props}
      >
        <div className="flex-shrink-0">
          {icon || getDefaultIcon()}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold mb-1">{title}</h4>}
          <div className="text-sm">{children}</div>
        </div>
        {closable && onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors"
            aria-label="Close alert"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }
);

// Display name for debugging
Alert.displayName = 'Alert';

export default Alert;
