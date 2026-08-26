/**
 * Agent World - Badge Component
 * Composant badge réutilisable du Design System
 * Conforme aux exigences US-060 : Design System
 */

import { forwardRef, HTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { BadgeVariant } from '../../../theme/types';

// Define badge props
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

// Badge component with forwardRef
const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      variant = 'default',
      size = 'md',
      dot = false,
      leftIcon,
      rightIcon,
      className,
      ...props
    },
    ref
  ) => {
    // Base badge classes
    const baseClasses = `
      inline-flex items-center gap-1.5
      font-medium
      rounded-full
      transition-colors duration-200
      gpu-accelerate
    `;

    // Variant classes
    const variantClasses = {
      default: `
        bg-surface-sunken
        text-text-secondary
      `,
      primary: `
        bg-primary-100
        text-primary-700
      `,
      secondary: `
        bg-secondary-100
        text-secondary-700
      `,
      success: `
        bg-success-100
        text-success-700
      `,
      warning: `
        bg-warning-100
        text-warning-700
      `,
      error: `
        bg-error-100
        text-error-700
      `,
      info: `
        bg-info-100
        text-info-700
      `,
    };

    // Size classes
    const sizeClasses = {
      sm: `px-2 py-0.5 text-xs`,
      md: `px-2.5 py-1 text-sm`,
      lg: `px-3 py-1.5 text-base`,
    };

    // Dot classes
    const dotClasses = `
      w-1.5 h-1.5 rounded-full
    `;

    // Dot color by variant
    const dotColorClasses = {
      default: 'bg-text-tertiary',
      primary: 'bg-primary-500',
      secondary: 'bg-secondary-500',
      success: 'bg-success-500',
      warning: 'bg-warning-500',
      error: 'bg-error-500',
      info: 'bg-info-500',
    };

    // Merge all classes
    const badgeClasses = twMerge(
      clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )
    );

    return (
      <span
        ref={ref}
        className={badgeClasses}
        {...props}
      >
        {dot && (
          <span
            className={clsx(dotClasses, dotColorClasses[variant])}
            aria-hidden="true"
          />
        )}
        {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
        {children}
        {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
      </span>
    );
  }
);

// Display name for debugging
Badge.displayName = 'Badge';

export default Badge;
