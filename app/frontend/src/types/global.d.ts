// Global type definitions for accessibility attributes

declare global {
  namespace React {
    interface HTMLAttributes<T> {
      inert?: string | undefined;
    }
  }
}

export {};