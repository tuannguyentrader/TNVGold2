"use client";

import { type ReactNode } from "react";
import { InfoTip } from "./InfoTip";

interface TechCardProps {
  label: string;
  value: string | ReactNode;
  note?: string;
  tooltip?: string;
  children?: ReactNode;
}

export function TechCard({ label, value, note, tooltip, children }: TechCardProps) {
  return (
    <article className="relative rounded-xl p-3.5 bg-[#0e131f] border border-white/5 hover:border-[#f5c542]/25 transition-all flex flex-col justify-between min-h-[105px]">
      {tooltip && <InfoTip text={tooltip} />}
      <div>
        <h4 className="text-[0.68rem] font-bold uppercase tracking-wider text-gray-400 mb-1">
          {label}
        </h4>
        <div className="text-base font-bold text-white font-mono tracking-tight">
          {value}
        </div>
      </div>
      <div>
        {note && (
          <p className="text-[0.68rem] text-gray-400 mt-1 leading-tight">
            {note}
          </p>
        )}
        {children}
      </div>
    </article>
  );
}
