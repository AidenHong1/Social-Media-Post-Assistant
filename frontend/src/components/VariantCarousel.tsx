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
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={() => setViewMode((v) => (v === "carousel" ? "grid" : "carousel"))}
          title={viewMode === "carousel" ? "切换到网格视图" : "切换到轮播视图"}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:border-slate-400"
        >
          <span className="text-sm">{viewMode === "carousel" ? "⊞" : "⇄"}</span>
          <span>{viewMode === "carousel" ? "网格视图" : "轮播视图"}</span>
        </button>
      </div>

      {viewMode === "grid" ? (
        <div className="grid gap-6 sm:grid-cols-2 2xl:grid-cols-3">
          {variants.map((v) => (
            <VariantCard key={v.id} variant={v} onRated={onRated} />
          ))}
        </div>
      ) : (
        <div className="relative">
          <div className="overflow-hidden rounded-lg" ref={emblaRef}>
            <div className="flex">
              {variants.map((v) => (
                <div key={v.id} className="min-w-0 flex-[0_0_100%] px-2">
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
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 flex h-10 w-10 items-center justify-center rounded-full border-2 border-slate-300 bg-white text-slate-700 text-xl font-light shadow-lg transition-all hover:bg-slate-50 hover:border-slate-400 hover:shadow-xl disabled:opacity-30 disabled:cursor-not-allowed"
              >
                ‹
              </button>
              <button
                type="button"
                onClick={scrollNext}
                disabled={selectedIndex === variants.length - 1}
                aria-label="下一个变体"
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 flex h-10 w-10 items-center justify-center rounded-full border-2 border-slate-300 bg-white text-slate-700 text-xl font-light shadow-lg transition-all hover:bg-slate-50 hover:border-slate-400 hover:shadow-xl disabled:opacity-30 disabled:cursor-not-allowed"
              >
                ›
              </button>

              <div className="mt-4 flex items-center justify-center gap-2">
                {variants.map((v, index) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => scrollTo(index)}
                    aria-label={`跳转到变体 ${index + 1}`}
                    className={`h-2 w-2 rounded-full transition-all ${
                      index === selectedIndex ? "bg-blue-600 w-6" : "bg-slate-300 hover:bg-slate-400"
                    }`}
                  />
                ))}
                <span className="ml-2 text-xs font-medium text-slate-500">
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
