interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  className?: string;
}

export function StatCard({
  title,
  value,
  icon,
  change,
  changeType = "neutral",
  className = "",
}: StatCardProps) {
  const changeColors = {
    positive: "text-green-600 dark:text-green-400",
    negative: "text-red-600 dark:text-red-400",
    neutral: "text-gray-500 dark:text-gray-400",
  };

  return (
    <div className={`card flex items-start justify-between ${className}`}>
      <div>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
          {title}
        </p>
        <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </p>
        {change && (
          <p className={`mt-1 text-xs ${changeColors[changeType]}`}>
            {change}
          </p>
        )}
      </div>
      <div className="rounded-lg bg-primary-50 p-3 dark:bg-primary-900/20">
        {icon}
      </div>
    </div>
  );
}
