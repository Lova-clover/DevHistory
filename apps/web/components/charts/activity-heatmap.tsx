'use client';

import { motion } from 'framer-motion';
import { Calendar } from 'lucide-react';
import { useMemo } from 'react';

interface ActivityHeatmapProps {
  data: Array<{ date: string; count: number }>;
}

export function ActivityHeatmap({ data }: ActivityHeatmapProps) {
  const heatmapData = useMemo(() => {
    // Generate last 365 days
    const today = new Date();
    const days = [];
    for (let i = 364; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      const activity = data.find((d) => d.date === dateStr);
      days.push({
        date: dateStr,
        count: activity?.count || 0,
        day: date.getDay(),
        week: Math.floor(i / 7),
      });
    }
    return days;
  }, [data]);

  const getColor = (count: number) => {
    if (count === 0) return 'bg-gray-100 dark:bg-gray-800';
    if (count < 3) return 'bg-green-200 dark:bg-green-900';
    if (count < 6) return 'bg-green-400 dark:bg-green-700';
    if (count < 9) return 'bg-green-600 dark:bg-green-500';
    return 'bg-green-800 dark:bg-green-400';
  };

  const weeks = 52;
  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-center gap-2 mb-6">
        <Calendar className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Activity Heatmap
        </h3>
        <span className="text-sm text-gray-600 dark:text-gray-400 ml-auto">
          365 days
        </span>
      </div>

      <div className="overflow-x-auto">
        <div className="flex gap-1">
          {/* Day labels */}
          <div className="flex flex-col gap-1 pr-2">
            {daysOfWeek.map((day, i) => (
              <div
                key={day}
                className="h-3 text-xs text-gray-500 dark:text-gray-400 flex items-center"
                style={{ opacity: i % 2 === 0 ? 1 : 0 }}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div className="flex gap-1">
            {Array.from({ length: weeks }).map((_, weekIndex) => (
              <div key={weekIndex} className="flex flex-col gap-1">
                {Array.from({ length: 7 }).map((_, dayIndex) => {
                  const dataIndex = weekIndex * 7 + dayIndex;
                  const day = heatmapData[dataIndex];
                  if (!day) return <div key={dayIndex} className="w-3 h-3" />;

                  return (
                    <motion.div
                      key={day.date}
                      whileHover={{ scale: 1.5 }}
                      className={`w-3 h-3 rounded-sm cursor-pointer ${getColor(day.count)}`}
                      title={`${day.date}: ${day.count} activities`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 mt-4 text-sm text-gray-600 dark:text-gray-400">
          <span>Less</span>
          <div className="flex gap-1">
            {[0, 3, 6, 9, 12].map((count) => (
              <div
                key={count}
                className={`w-3 h-3 rounded-sm ${getColor(count)}`}
              />
            ))}
          </div>
          <span>More</span>
        </div>
      </div>
    </motion.div>
  );
}
