import type { ContentSegment, PlatformName } from "../types";

interface Props {
  platform: PlatformName;
  segments: ContentSegment[];
}

const PLATFORM_STYLES: Record<PlatformName, {
  outer: string;
  card: string;
  text: string;
}> = {
  linkedin: {
    outer: "rounded-xl bg-[#f3f2ef] p-3 sm:p-4",
    card: "rounded-lg bg-white p-5 shadow-sm",
    text: "font-['Segoe_UI',system-ui,sans-serif] text-[14px] leading-relaxed text-slate-800",
  },
  facebook: {
    outer: "rounded-xl bg-[#f0f2f5] p-3 sm:p-4",
    card: "rounded-lg bg-white p-4",
    text: "font-['Helvetica',system-ui,sans-serif] text-[15px] leading-relaxed text-slate-800",
  },
};

export default function PlatformPostCard({ platform, segments }: Props) {
  const style = PLATFORM_STYLES[platform] ?? PLATFORM_STYLES.linkedin;

  return (
    <div className={style.outer}>
      <div className={style.card}>
        {segments.map((segment, index) => (
          <div key={index}>
            {segment.type === "text" ? (
              <p className={`${style.text} mb-3 whitespace-pre-wrap break-words last:mb-0`}>
                {segment.content}
              </p>
            ) : (
              <div className="mb-3 last:mb-0">
                <img
                  src={segment.url}
                  alt={segment.caption ?? ""}
                  className="w-full max-h-80 rounded-md object-cover"
                />
                {segment.caption && (
                  <p className="mt-1 text-xs text-slate-500">{segment.caption}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
