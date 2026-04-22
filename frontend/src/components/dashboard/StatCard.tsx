import React from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  gradient?: string;
  dark?: boolean;
  icon?: string;
  trend?: string;
  onClick?: () => void;
  numbered?: string;
  accent?: boolean;
}

export default function StatCard({ label, value, sublabel, dark, icon, trend, onClick, numbered, accent }: StatCardProps) {
  const bg = dark ? "bg-[#111111]" : accent ? "bg-[#E8D44D]" : "bg-white";
  const textColor = dark ? "text-white" : accent ? "text-[#111111]" : "text-gray-900";
  const subColor = dark ? "text-white/50" : accent ? "text-[#111111]/60" : "text-gray-400";

  return (
    <div
      onClick={onClick}
      className={`relative rounded-2xl p-5 ${bg} shadow-[0_1px_4px_rgba(0,0,0,0.07)] overflow-hidden ${onClick ? "cursor-pointer transition-all duration-200 hover:shadow-[0_4px_16px_rgba(0,0,0,0.10)] hover:-translate-y-0.5" : ""}`}
    >
      {numbered && (
        <span className={`absolute top-3 right-3 text-[10px] font-semibold px-2 py-0.5 rounded-full ${dark ? "bg-white/10 text-white/50" : accent ? "bg-black/10 text-black/40" : "bg-gray-100 text-gray-400"}`}>
          {numbered}
        </span>
      )}
      {icon && <div className={`text-xl mb-2 ${textColor}`}>{icon}</div>}
      <div className={`text-4xl font-bold tracking-tight ${textColor}`}>{value}</div>
      <div className={`text-sm font-medium mt-1 ${textColor}`}>{label}</div>
      {sublabel && <div className={`text-xs mt-0.5 ${subColor}`}>{sublabel}</div>}
      {trend && (
        <div className={`text-xs mt-3 flex items-center gap-1 ${subColor}`}>
          <span>↗</span><span>{trend}</span>
        </div>
      )}
    </div>
  );
}
