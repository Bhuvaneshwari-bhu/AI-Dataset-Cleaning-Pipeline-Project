import { useEffect, useRef, useState } from 'react';
import Badge from '../ui/Badge';

function getColor(score) {
  if (score >= 80) return { stroke: '#2E8B57', badge: 'success', label: 'Excellent' };
  if (score >= 60) return { stroke: '#D4A017', badge: 'warning', label: 'Moderate' };
  return { stroke: '#C0392B', badge: 'danger', label: 'Poor' };
}

export default function QualityGauge({ score = 0, passed = false }) {
  const [animated, setAnimated] = useState(0);
  const rafRef = useRef(null);

  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const { stroke, badge, label } = getColor(score);
  const offset = circumference - (animated / 100) * circumference;

  useEffect(() => {
    const start = performance.now();
    const duration = 1200;
    const tick = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimated(eased * score);
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [score]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <svg width="180" height="180" className="-rotate-90">
          {/* Track */}
          <circle
            cx="90" cy="90" r={radius}
            fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="14"
          />
          {/* Progress */}
          <circle
            cx="90" cy="90" r={radius}
            fill="none" stroke={stroke} strokeWidth="14"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 8px ${stroke}66)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold text-ink leading-none">
            {animated.toFixed(1)}
          </span>
          <span className="text-xs text-ink-muted font-medium mt-0.5">/ 100</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Badge color={badge}>{label}</Badge>
        <Badge color={passed ? 'success' : 'danger'}>
          {passed ? '✓ Passed' : '✗ Failed'}
        </Badge>
      </div>
    </div>
  );
}
