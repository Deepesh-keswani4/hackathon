import React from "react";

interface Leave {
  id: number;
  leave_type: string;
  from_date: string;
  to_date: string;
  days_count: number;
  status: string;
  reason: string;
  is_half_day?: boolean;
  employee_name?: string;
  applied_by_name?: string;
}

interface LeaveTableProps {
  leaves: Leave[];
  loading: boolean;
  isManager?: boolean;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onCancel?: (id: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-700",
  APPROVED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-600",
  CANCELLED: "bg-gray-100 text-gray-500",
};

const TYPE_LABELS: Record<string, string> = {
  CL: "Casual", SL: "Sick", PL: "Privilege", LOP: "LOP", CO: "Comp Off",
};

export default function LeaveTable({ leaves, loading, isManager, onApprove, onReject, onCancel }: LeaveTableProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-16 rounded-2xl bg-white/40 animate-pulse" />
        ))}
      </div>
    );
  }

  if (leaves.length === 0) {
    return (
      <div className="py-12 text-center">
        <div className="text-4xl mb-3">🌿</div>
        <p className="text-gray-400 text-sm">No leave requests found</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {leaves.map(lv => (
        <div
          key={lv.id}
          className="flex items-center gap-4 p-4 rounded-2xl bg-white/50 hover:bg-white/80 transition-colors group"
        >
          {/* Type badge */}
          <div className="w-16 flex-shrink-0">
            <span className="px-2 py-1 rounded-lg bg-gray-900 text-white text-xs font-bold">
              {TYPE_LABELS[lv.leave_type] || lv.leave_type}
            </span>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            {isManager && lv.employee_name && (
              <div className="text-xs font-bold text-gray-900">{lv.employee_name}</div>
            )}
            <div className="text-sm text-gray-700 font-medium">
              {lv.from_date} → {lv.to_date}
              {lv.is_half_day && <span className="ml-1 text-xs text-gray-400">(half day)</span>}
            </div>
            <div className="text-xs text-gray-400 truncate">{lv.reason}</div>
          </div>

          {/* Days */}
          <div className="text-sm font-bold text-gray-900 flex-shrink-0">
            {lv.days_count}d
          </div>

          {/* Status */}
          <div className="flex-shrink-0">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[lv.status] || "bg-gray-100 text-gray-500"}`}>
              {lv.status}
            </span>
          </div>

          {/* Actions */}
          <div className="flex gap-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            {isManager && lv.status === "PENDING" && (
              <>
                <button
                  onClick={() => onApprove?.(lv.id)}
                  className="px-3 py-1.5 bg-gray-900 text-white text-xs font-semibold rounded-full hover:bg-gray-700 transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => onReject?.(lv.id)}
                  className="px-3 py-1.5 bg-red-500 text-white text-xs font-semibold rounded-full hover:bg-red-600 transition-colors"
                >
                  Reject
                </button>
              </>
            )}
            {!isManager && lv.status === "PENDING" && (
              <button
                onClick={() => onCancel?.(lv.id)}
                className="px-3 py-1.5 border border-gray-200 text-gray-500 text-xs font-semibold rounded-full hover:border-red-300 hover:text-red-500 transition-colors"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
