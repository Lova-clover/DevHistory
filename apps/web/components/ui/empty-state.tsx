'use client';

import { motion } from 'framer-motion';
import { FileQuestion, RefreshCw } from 'lucide-react';
import { Button } from './button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center justify-center py-16 px-4"
    >
      <motion.div
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
        className="mb-6"
      >
        {icon || (
          <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <FileQuestion className="w-10 h-10 text-gray-400 dark:text-gray-600" />
          </div>
        )}
      </motion.div>

      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 text-center max-w-md mb-6">
        {description}
      </p>

      {action && (
        <Button
          onClick={action.onClick}
          leftIcon={<RefreshCw className="w-4 h-4" />}
        >
          {action.label}
        </Button>
      )}
    </motion.div>
  );
}
