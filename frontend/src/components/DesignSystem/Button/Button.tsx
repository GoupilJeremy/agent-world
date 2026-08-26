/**
 * Agent World - Button Component
 * Composant bouton réutilisable du Design System
 * Conforme aux exigences US-060 : Design System
 */

import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ButtonVariant, ButtonSize } from '../../../theme/types';

// Define button props
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  isLoading?: boolean;
  fullWidth?: boolean;
  asChild?: boolean;
}

// Button component with forwardRef
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      leftIcon,
      rightIcon,
      isLoading = false,
      fullWidth = false,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    // Base button classes
    const baseClasses = `
      inline-flex items-center justify-center
      font-medium
      rounded-lg
      transition-all duration-200
      focus:outline-none
      focus:ring-2 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      gpu-accelerate
    `;

    // Variant classes
    const variantClasses = {
      primary: `
        bg-primary-500 text-white
        hover:bg-primary-600
        active:bg-primary-700
        focus:ring-primary-500
        shadow-sm hover:shadow-md
      `,
      secondary: `
        bg-secondary-500 text-white
        hover:bg-secondary-600
        active:bg-secondary-700
        focus:ring-secondary-500
        shadow-sm hover:shadow-md
      `,
      ghost: `
        bg-transparent text-text-primary
        hover:bg-surface-sunken
        active:bg-surface-sunken
        focus:ring-border-primary
      `,
      outline: `
        bg-transparent text-text-primary
        border border-border-primary
        hover:bg-surface-sunken
        active:bg-surface-sunken
        focus:ring-border-primary
      `,
      danger: `
        bg-error-500 text-white
        hover:bg-error-600
        active:bg-error-700
        focus:ring-error-500
        shadow-sm hover:shadow-md
      `,
      success: `
        bg-success-500 text-white
        hover:bg-success-600
        active:bg-success-700
        focus:ring-success-500
        shadow-sm hover:shadow-md
      `,
    };

    // Size classes
    const sizeClasses = {
      sm: `
        px-3 py-1.5
        text-sm
        gap-1.5
        h-8
      `,
      md: `
        px-4 py-2
        text-sm
        gap-2
        h-9
      `,
      lg: `
        px-6 py-2.5
        text-base
        gap-2.5
        h-10
      `,
    };

    // Merge all classes with tailwind-merge for better handling
    const buttonClasses = twMerge(
      clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        isLoading && 'cursor-wait',
        className
      )
    );

    // Loading spinner component
    const Spinner = () => (
      <svg
        className="animate-spin h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <Spinner />
            {children && <span>{children}</span>}
          </>
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

// Display name for debugging
Button.displayName = 'Button';

export default Button;
