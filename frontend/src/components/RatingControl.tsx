import { useState } from "react";

interface Props {
  score: number;
  isFavorite: boolean;
  onRate: (score: number, isFavorite: boolean) => void;
}

export default function RatingControl({ score, isFavorite, onRate }: Props) {
  const [hoverScore, setHoverScore] = useState<number | null>(null);
  const displayScore = hoverScore ?? score;

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onMouseEnter={() => setHoverScore(n)}
            onMouseLeave={() => setHoverScore(null)}
            onClick={() => onRate(n, isFavorite)}
            className={`text-lg transition-all hover:scale-110 ${n <= displayScore ? "text-yellow-400" : "text-slate-300 hover:text-yellow-200"}`}
            aria-label={`评${n}分`}
          >
            ★
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => onRate(score || 0, !isFavorite)}
        className={`text-xl transition-all hover:scale-110 ${isFavorite ? "text-pink-500" : "text-slate-300 hover:text-pink-300"}`}
        aria-label={isFavorite ? "取消收藏" : "收藏"}
        title={isFavorite ? "取消收藏" : "收藏"}
      >
        {isFavorite ? "♥" : "♡"}
      </button>
    </div>
  );
}
