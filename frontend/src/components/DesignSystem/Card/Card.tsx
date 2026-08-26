/**
 * Agent World - Card Component
 * Composant carte réutilisable du Design System
 * Conforme aux exigences US-060 : Design System
 */

import { forwardRef, HTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { CardVariant } from '../../../theme/types';

// Define card props
export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  header?: ReactNode;
  footer?: ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

// Card component with forwardRef
const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      header,
      footer,
      padding = 'md',
      hoverable = false,
      clickable = false,
      onClick,
      className,
      ...props
    },
    ref
  ) => {
    // Base card classes
    const baseClasses = `
      rounded-xl
      transition-all duration-200
      gpu-accelerate
    `;

    // Variant classes
    const variantClasses = {
      default: `
        bg-surface-elevated
        border border-border-primary
      `,
      elevated: `
        bg-surface-elevated
        shadow-md
        border border-border-primary
      `,
      sunken: `
        bg-surface-sunken
        border border-border-secondary
      `,
      bordered: `
        bg-surface
        border-2 border-border-primary
      `,
    };

    // Padding classes
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    // Merge all classes
    const cardClasses = twMerge(
      clsx(
        baseClasses,
        variantClasses[variant],
        paddingClasses[padding],
        hoverable && 'hover:shadow-lg hover:-translate-y-1',
        clickable && 'cursor-pointer active:scale-[0.98]',
        className
      )
    );

    return (
      <div
        ref={ref}
        className={cardClasses}
        onClick={clickable ? onClick : undefined}
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        {...props}
      >
        {header && (
          <div className="mb-4 pb-4 border-b border-border-secondary">
            {header}
          </div>
        )}
        {children}
        {footer && (
          <div className="mt-4 pt-4 border-t border-border-secondary">
            {footer}
          </div>
        )}
      </div>
    );
  }
);

// Display name for debugging
Card.displayName = 'Card';

export default Card;
