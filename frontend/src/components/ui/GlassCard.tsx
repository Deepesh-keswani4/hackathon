import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  dark?: boolean;
  onClick?: () => void;
  hover?: boolean;
  numbered?: string;
}

export default function GlassCard({ children, className = "", dark = false, onClick, hover = false, numbered }: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={`
        relative rounded-2xl p-5
        ${dark ? "bg-[#111111] text-white" : "bg-white text-gray-900"}
        shadow-[0_1px_4px_rgba(0,0,0,0.07)]
        ${hover || onClick ? "cursor-pointer transition-all duration-200 hover:shadow-[0_4px_16px_rgba(0,0,0,0.10)] hover:-translate-y-0.5" : ""}
        ${className}
      `}
    >
      {numbered && (
        <span className={`absolute top-4 left-4 text-[10px] font-semibold px-2 py-0.5 rounded-full ${dark ? "bg-white/10 text-white/50" : "bg-gray-100 text-gray-400"}`}>
          {numbered}
        </span>
      )}
      {children}
    </div>
  );
}
