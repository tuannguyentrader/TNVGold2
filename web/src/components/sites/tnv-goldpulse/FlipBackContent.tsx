"use client";

interface MultiTfRow {
  tf: string;
  value: string;
  badge?: string;
  badgeType?: "up" | "down" | "neutral";
}

interface FlipBackContentProps {
  label: string;
  rows: MultiTfRow[];
}

export function FlipBackContent({ label, rows }: FlipBackContentProps) {
  return (
    <div className="flex flex-col justify-between h-full w-full">
      <div className="flex items-center justify-between text-[0.68rem] font-bold uppercase tracking-wider text-gray-400 mb-0.5">
        <span>{label}</span>
      </div>

      <div className="space-y-0.5 my-auto">
        {rows.map((row) => (
          <div
            className="flex items-center justify-between text-[0.7rem] py-0.5 border-b border-white/5 last:border-none"
            key={row.tf}
          >
            <span className="font-mono text-gray-400 text-[0.68rem]">{row.tf}</span>
            <div className="flex items-center gap-1.5">
              {/* Value: luôn tô màu theo badgeType */}
              <span
                className={`font-semibold text-[0.72rem] ${
                  row.badgeType === "up"
                    ? "text-[#61e294]"
                    : row.badgeType === "down"
                    ? "text-[#ff8383]"
                    : "text-white"
                }`}
              >
                {row.value}
              </span>
              {/* Chỉ hiển thị badge khi khác value */}
              {row.badge && row.badge !== row.value && (
                <span
                  className={`text-[0.58rem] px-1.5 py-0.2 rounded font-bold uppercase ${
                    row.badgeType === "up"
                      ? "bg-[rgba(97,226,148,0.15)] text-[#61e294] border border-[rgba(97,226,148,0.3)]"
                      : row.badgeType === "down"
                      ? "bg-[rgba(255,96,96,0.15)] text-[#ff8383] border border-[rgba(255,96,96,0.3)]"
                      : "bg-white/10 text-gray-300"
                  }`}
                >
                  {row.badge}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="text-[0.6rem] text-gray-500 hover:text-[#f5c542] text-right font-mono transition-colors">
        Tap &#8617;
      </div>
    </div>
  );
}
