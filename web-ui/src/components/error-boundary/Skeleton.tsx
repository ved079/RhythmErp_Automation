'use client';

import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', width, height }) => {
  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`bg-gray-200 dark:bg-gray-700 rounded animate-pulse ${className}`}
      style={style}
    />
  );
};

export const SkeletonText: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="space-y-2">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} className="h-4 w-full" />
    ))}
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({ rows = 5, columns = 4 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-4">
        {Array.from({ length: columns }).map((_, j) => (
          <Skeleton key={j} className="h-8 flex-1" />
        ))}
      </div>
    ))}
  </div>
);

export const SkeletonCard: React.FC = () => (
  <div className="p-4 border rounded-lg space-y-3">
    <Skeleton className="h-32 w-full" />
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-1/2" />
  </div>
);
