// scroll-scrub-hero.tsx — starting template for the "Scroll-scrub film" pattern
// (wow-maker.md §2). Adapt to the brief: file paths, mood/colors, caption copy,
// pin height. Read references/step-4-build-scroll-scrub.md alongside this file —
// it explains *why* each piece exists, this file is just the *what*.
//
// Usage in a route:
//   import { ClientOnly } from "~/components/client-only";
//   import { ScrollScrubHero } from "~/components/scroll-scrub-hero";
//   <ClientOnly fallback={<StaticHeroFallback />}>
//     <ScrollScrubHero
//       framesBasePath="/frames/product"
//       manifest={manifest} // import the manifest.json written by extract-frames.sh
//       captions={[
//         { fromProgress: 0.05, toProgress: 0.25, content: <h2>Introducing.</h2> },
//         { fromProgress: 0.4, toProgress: 0.6, content: <p>Engineered from a single block.</p> },
//         { fromProgress: 0.75, toProgress: 0.95, content: <p>Available now.</p> },
//       ]}
//     />
//   </ClientOnly>

import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface FrameManifest {
  frameCount: number;
  width: number;
  height: number;
  pattern: string; // e.g. "frame-%04d.jpg"
}

interface Caption {
  fromProgress: number;
  toProgress: number;
  content: React.ReactNode;
}

interface ScrollScrubHeroProps {
  framesBasePath: string; // e.g. "/frames/product" — served from app/public/frames/product
  manifest: FrameManifest;
  captions?: Caption[];
  pinVh?: number; // how many viewport-heights tall the pinned scroll range is; default 3
}

function frameUrl(basePath: string, pattern: string, index1Based: number) {
  const padded = String(index1Based).padStart(4, "0");
  return `${basePath}/${pattern.replace("%04d", padded)}`;
}

export function ScrollScrubHero({
  framesBasePath,
  manifest,
  captions = [],
  pinVh = 3,
}: ScrollScrubHeroProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<(HTMLImageElement | null)[]>([]);
  const currentDrawnRef = useRef<number>(-1);
  const [ready, setReady] = useState(false);
  const [progress, setProgress] = useState(0);
  const reducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --- preload: block on a small head window, stream the rest in the background ---
  useEffect(() => {
    const { frameCount, pattern } = manifest;
    imagesRef.current = new Array(frameCount).fill(null);
    const HEAD_WINDOW = Math.min(10, frameCount);

    let cancelled = false;

    function loadFrame(i: number) {
      const img = new Image();
      img.src = frameUrl(framesBasePath, pattern, i + 1);
      imagesRef.current[i] = img;
      return new Promise<void>((resolve) => {
        img.onload = () => resolve();
        img.onerror = () => resolve(); // don't block the rest of the sequence on one bad frame
      });
    }

    async function run() {
      const head = Array.from({ length: HEAD_WINDOW }, (_, i) => loadFrame(i));
      await Promise.all(head);
      if (cancelled) return;
      setReady(true);

      for (let i = HEAD_WINDOW; i < frameCount; i++) {
        if (cancelled) return;
        await loadFrame(i);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [framesBasePath, manifest]);

  // --- ScrollTrigger: drive progress from the pinned section, not raw scrollY ---
  useEffect(() => {
    if (!ready || reducedMotion || !containerRef.current) return;

    const trigger = ScrollTrigger.create({
      trigger: containerRef.current,
      start: "top top",
      end: `+=${pinVh * 100}%`,
      pin: true,
      scrub: true, // no easing — must track the scrollbar 1:1
      onUpdate: (self) => setProgress(self.progress),
    });

    return () => trigger.kill();
  }, [ready, reducedMotion, pinVh]);

  // --- draw: guard against not-yet-loaded frames by drawing the nearest loaded one ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !ready) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const targetIndex = reducedMotion
      ? Math.floor(manifest.frameCount / 2)
      : Math.round(progress * (manifest.frameCount - 1));

    let drawIndex = targetIndex;
    while (drawIndex >= 0 && !imagesRef.current[drawIndex]?.complete) drawIndex--;
    if (drawIndex < 0) drawIndex = targetIndex;
    if (drawIndex === currentDrawnRef.current) return;

    const img = imagesRef.current[drawIndex];
    if (!img) return;

    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth;
    const cssHeight = canvas.clientHeight;
    if (canvas.width !== cssWidth * dpr || canvas.height !== cssHeight * dpr) {
      canvas.width = cssWidth * dpr;
      canvas.height = cssHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    ctx.clearRect(0, 0, cssWidth, cssHeight);
    ctx.drawImage(img, 0, 0, cssWidth, cssHeight);
    currentDrawnRef.current = drawIndex;
  }, [progress, ready, reducedMotion, manifest.frameCount]);

  return (
    <div
      ref={containerRef}
      className="relative h-[100vh] w-full overflow-hidden bg-[var(--hero-bg,#0a0a0a)]"
    >
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      {!reducedMotion &&
        captions.map((caption, i) => {
          const inRange =
            progress >= caption.fromProgress && progress <= caption.toProgress;
          return (
            <div
              key={i}
              className="pointer-events-none absolute inset-0 flex items-center justify-center text-center transition-opacity duration-300"
              style={{ opacity: inRange ? 1 : 0 }}
            >
              {caption.content}
            </div>
          );
        })}
    </div>
  );
}

// Server-rendered fallback (used inside <ClientOnly fallback={...}>) and the
// prefers-reduced-motion resting state both want the same thing: one static frame,
// no canvas, no scroll listener.
export function StaticHeroFallback({
  frameSrc,
  className,
}: {
  frameSrc: string;
  className?: string;
}) {
  return (
    <div className={`relative h-[100vh] w-full overflow-hidden bg-[var(--hero-bg,#0a0a0a)] ${className ?? ""}`}>
      <img src={frameSrc} alt="" className="absolute inset-0 h-full w-full object-cover" />
    </div>
  );
}
