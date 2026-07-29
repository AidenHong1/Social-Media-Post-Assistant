import { useCallback, useEffect, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import type { VariantOut } from "../types";
import VariantCard from "./VariantCard";

interface Props {
  variants: VariantOut[];
  onRated: (variantId: number, score: number, isFavorite: boolean) => void;
}

export default function VariantCarousel({ variants, onRated }: Props) {
  const [viewMode, setViewMode] = useState<"carousel" | "grid">("carousel");
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: false });
  const [selectedIndex, setSelectedIndex] = useState(0);

  const scrollTo = useCallback((index: number) => emblaApi?.scrollTo(index), [emblaApi]);
  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi]);
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;
    const onSelect = () => setSelectedIndex(emblaApi.selectedScrollSnap());
    emblaApi.on("select", onSelect);
    onSelect();
    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={() => setViewMode((v) => (v === "carousel" ? "grid" : "carousel"))}
          title={viewMode === "carousel" ? "切换到网格视图" : "切换到轮播视图"}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
        >
          {viewMode === "carousel" ? "⊞ 网格视图" : "⇄ 轮播视图"}
        </button>
      </div>

      {viewMode === "grid" ? (
        <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-3">
          {variants.map((v) => (
            <VariantCard key={v.id} variant={v} onRated={onRated} />
          ))}
        </div>
      ) : (
        <div className="relative">
          <div className="overflow-hidden" ref={emblaRef}>
            <div className="flex">
              {variants.map((v) => (
                <div key={v.id} className="min-w-0 flex-[0_0_100%] px-1">
                  <VariantCard variant={v} onRated={onRated} />
                </div>
              ))}
            </div>
          </div>

          {variants.length > 1 && (
            <>
              <button
                type="button"
                onClick={scrollPrev}
                disabled={selectedIndex === 0}
                aria-label="上一个变体"
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3 flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-30"
              >
                ‹
              </button>
              <button
                type="button"
                onClick={scrollNext}
                disabled={selectedIndex === variants.length - 1}
                aria-label="下一个变体"
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3 flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-30"
              >
                ›
              </button>

              <div className="mt-2 flex items-center justify-center gap-2">
                {variants.map((v, index) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => scrollTo(index)}
                    aria-label={`跳转到变体 ${index + 1}`}
                    className={`h-2 w-2 rounded-full transition-colors ${
                      index === selectedIndex ? "bg-blue-600" : "bg-slate-300 hover:bg-slate-400"
                    }`}
                  />
                ))}
                <span className="ml-2 text-xs text-slate-400">
                  {selectedIndex + 1} / {variants.length}
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
