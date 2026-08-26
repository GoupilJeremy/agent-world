/**
 * Agent World - Input Component
 * Composant input réutilisable du Design System
 * Conforme aux exigences US-060 : Design System
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { InputVariant, InputSize } from '../../../theme/types';

// Define input props
export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant;
  size?: InputSize;
  label?: string;
  errorMessage?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

// Input component with forwardRef
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      variant = 'default',
      size = 'md',
      label,
      errorMessage,
      leftIcon,
      rightIcon,
      fullWidth = true,
      className,
      disabled,
      id,
      type = 'text',
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    // Base input classes
    const baseClasses = `
      w-full
      rounded-lg
      transition-all duration-200
      focus:outline-none
      disabled:opacity-50 disabled:cursor-not-allowed
      placeholder:text-text-tertiary
      gpu-accelerate
    `;

    // Variant classes
    const variantClasses = {
      default: `
        bg-surface
        border border-border-primary
        text-text-primary
        focus:border-primary-500
        focus:ring-2 focus:ring-primary-500/20
        hover:border-border-secondary
      `,
      error: `
        bg-surface
        border border-error-500
        text-text-primary
        focus:border-error-600
        focus:ring-2 focus:ring-error-500/20
        hover:border-error-600
      `,
      success: `
        bg-surface
        border border-success-500
        text-text-primary
        focus:border-success-600
        focus:ring-2 focus:ring-success-500/20
        hover:border-success-600
      `,
    };

    // Size classes
    const sizeClasses = {
      sm: `
        px-3 py-2
        text-sm
        gap-2
        h-8
      `,
      md: `
        px-4 py-2.5
        text-base
        gap-2.5
        h-9
      `,
      lg: `
        px-5 py-3
        text-lg
        gap-3
        h-11
      `,
    };

    // Icon classes
    const iconClasses = {
      sm: 'w-4 h-4',
      md: 'w-5 h-5',
      lg: 'w-6 h-6',
    };

    // Merge all classes
    const inputClasses = twMerge(
      clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        leftIcon && 'pl-10',
        rightIcon && 'pr-10',
        !leftIcon && !rightIcon && !fullWidth && 'inline-flex',
        fullWidth && 'block',
        className
      )
    );

    // Container classes
    const containerClasses = clsx(
      'relative',
      !fullWidth && 'inline-flex',
      fullWidth && 'w-full'
    );

    // Label classes
    const labelClasses = clsx(
      'block',
      'text-sm font-medium text-text-secondary',
      'mb-1.5'
    );

    // Error message classes
    const errorMessageClasses = clsx(
      'mt-1.5',
      'text-sm text-error-500',
      'min-h-[1.25rem]' // Ensure space is reserved
    );

    // Icon wrapper classes
    const iconWrapperClasses = clsx(
      'absolute',
      'flex items-center justify-center',
      'pointer-events-none',
      leftIcon ? 'left-3' : 'right-3'
    );

    return (
      <div className={containerClasses}>
        {label && (
          <label htmlFor={inputId} className={labelClasses}>
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className={iconWrapperClasses}>
              <span className={iconClasses[size]}>{leftIcon}</span>
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            type={type}
            className={inputClasses}
            disabled={disabled}
            aria-invalid={variant === 'error'}
            aria-describedby={variant === 'error' ? `${inputId}-error` : undefined}
            {...props}
          />
          
          {rightIcon && (
            <div className={iconWrapperClasses}>
              <span className={iconClasses[size]}>{rightIcon}</span>
            </div>
          )}
        </div>
        
        {variant === 'error' && errorMessage && (
          <p id={`${inputId}-error`} className={errorMessageClasses} role="alert">
            {errorMessage}
          </p>
        )}
        
        {variant === 'success' && !errorMessage && (
          <p className={clsx(errorMessageClasses, 'text-success-500')} role="status">
            {props['aria-label'] || 'Validation réussie'}
          </p>
        )}
      </div>
    );
  }
);

// Display name for debugging
Input.displayName = 'Input';

export default Input;
