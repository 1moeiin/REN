/**
 * Cinematic hero — the homepage's opening shot.
 *
 * One camera move down the building, scrubbed by scroll: the crown from the
 * air, a descent into the cloud deck, the REN wordmark surfacing inside it,
 * the deck clearing onto the lower floors, and the shot coming to rest at the
 * entrance. Markup: main/_cinematic_hero.html · styles: static/src/input.css.
 *
 * The film is a pure function of one number, shot.t (0 → 1), which a single
 * ScrollTrigger scrubs across its track. Nothing is sequenced: every layer reads t
 * and works out where it should be. Scrolling back simply replays the same
 * frames in reverse, and scenes can overlap freely — which is what keeps it
 * reading as one continuous take rather than a string of animations:
 *
 *   0.00 ─ 0.04  cue        the scroll cue clears as soon as the shot starts
 *   0.03 ─ 0.22  title      the headline, set in the sky above the clouds,
 *                           rides up with it and is gone before the deck
 *   0.00 ─ 1.00  camera     one descent, fastest while hidden in the fog
 *   0.30 ─ 0.56  approach   haze thickens; the first banks rise into frame
 *   0.50 ─ 0.62  immersion  fog closes over the lens
 *   0.58 ─ 0.72  reveal     REN surfaces through the fog, blur 12px → 0
 *   0.72 ─ 0.80  recede     the fog rolls back over the word
 *   0.76 ─ 0.94  clearing   banks part; near veils rush past the lens
 *   0.88 ─ 1.00  arrival    the ground fade hands over to the next section
 *
 * Only transform, opacity and filter change per frame, and only while the
 * scrub is moving — there is no loop of its own.
 */

const SCENE = {
  cue: [0, 0.04],
  title: [0.03, 0.22],
  haze: [0.3, 0.56, 0.8, 0.92],
  fogBack: [0.5, 0.6, 0.78, 0.86],
  reveal: [0.58, 0.7],
  recede: [0.72, 0.8],
  clearing: [0.76, 0.94],
  ground: [0.88, 1],
};

/* Where the descent is fastest — inside the fog, where nobody can see it. */
const PEAK = 0.66;

/* Zoom keyframes [t, scale]: a slow push toward the facade on the way down,
   easing back as the clouds part, then a last settle on the entrance. */
const ZOOM = [[0, 1], [0.62, 1.12], [0.86, 1.03], [1, 1.07]];

/* The sky copy travels at (1 − SKY_DRIFT) of the tower's speed. */
const SKY_DRIFT = 0.45;

/* The cloud deck. alt: the height in the render (0 crown … 1 base) a cloud
   floats at, so the camera descends *through* the deck. depth: parallax
   against the building (1 = the tower's plane, > 1 nearer the lens). x and
   part are in vw — resting offset, and how far it drifts aside as the deck
   clears. grow: how much a near cloud swells as it passes the lens.
   in/out: fade windows, so the story keeps its timing on any screen.
   yield: for the clouds in front of the wordmark — how far they thin while
   they part around it, so REN surfaces between them rather than through a
   wall, before they close over it again. */
const CLOUDS = {
  "far-l": { alt: 0.5, depth: 0.7, x: -26, scale: 0.9, part: -8, grow: 0, in: [0.36, 0.5], out: [0.84, 0.94] },
  "far-r": { alt: 0.57, depth: 0.8, x: 30, scale: 0.8, part: 10, grow: 0, in: [0.4, 0.54], out: [0.84, 0.94], flip: true },
  "mid-l": { alt: 0.58, depth: 1.2, x: -20, scale: 1, part: -46, grow: 0.1, yield: 0.86, in: [0.44, 0.56], out: [0.82, 0.92] },
  "mid-r": { alt: 0.64, depth: 1.3, x: 22, scale: 1.1, part: 48, grow: 0.1, yield: 0.86, in: [0.46, 0.58], out: [0.82, 0.92], flip: true },
  "near-l": { alt: 0.62, depth: 2, x: -12, scale: 1, part: -60, grow: 0.7, yield: 1, in: [0.5, 0.6], out: [0.8, 0.9] },
  "near-r": { alt: 0.7, depth: 2.3, x: 14, scale: 1.1, part: 64, grow: 0.7, yield: 1, in: [0.52, 0.62], out: [0.82, 0.92], flip: true },
};

/* ---------------------------------------------------------------- helpers */

const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);

const smooth = (a, b, t) => {
  const x = clamp01((t - a) / (b - a));
  return x * x * (3 - 2 * x);
};

/** Rises over [a, b], holds, falls over [c, d]. */
const envelope = (t, [a, b, c, d]) => smooth(a, b, t) * (1 - smooth(c, d, t));

/**
 * Camera progress. Half of it is linear, so the camera answers the very first
 * scroll; the other half is two quadratic halves meeting at PEAK with equal
 * speed, so it surges while hidden in the fog and eases into the arrival.
 */
const descent = (t) =>
  0.5 * t + 0.5 * (t < PEAK ? PEAK * (t / PEAK) ** 2 : 1 - (1 - PEAK) * ((1 - t) / (1 - PEAK)) ** 2);

function keyframed(frames, t) {
  for (let i = 1; i < frames.length; i++) {
    const [t1, v1] = frames[i];
    if (t <= t1) {
      const [t0, v0] = frames[i - 1];
      return v0 + (v1 - v0) * smooth(t0, t1, t);
    }
  }
  return frames[frames.length - 1][1];
}

function show(el, opacity) {
  el.style.opacity = opacity.toFixed(3);
  el.style.visibility = opacity > 0.002 ? "visible" : "hidden";
}

/** Resolves once the render is loaded and decoded; rejects if it is broken. */
function imageReady(img) {
  const loaded = img.complete
    ? img.naturalWidth ? Promise.resolve() : Promise.reject(new Error("hero image failed"))
    : new Promise((resolve, reject) => {
        img.addEventListener("load", resolve, { once: true });
        img.addEventListener("error", reject, { once: true });
      });
  // decode() keeps the first frame from painting half-decoded, but it can
  // stall in a background tab, or reject for a cached image. Neither should
  // hold the film back, so it gets a moment and no more.
  const moment = new Promise((resolve) => setTimeout(resolve, 1200));
  return loaded.then(() => Promise.race([img.decode?.().catch(() => {}), moment]));
}

/**
 * Reads the render once, at thumbnail size: the colours down its outer edges
 * (to extend it past its own sides on very wide screens) and whether its
 * flanks above the horizon are clean sky — the sky drift is only safe then.
 */
function sampleRender(img, frac) {
  const W = 48;
  const H = 96;
  const ctx = Object.assign(document.createElement("canvas"), { width: W, height: H })
    .getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, W, H);

  let data;
  try {
    data = ctx.getImageData(0, 0, W, H).data;
  } catch {
    return { edges: null, skyClean: false }; // cross-origin media: skip, don't break
  }
  const px = (x, y) => {
    const i = (y * W + x) * 4;
    return [data[i], data[i + 1], data[i + 2]];
  };

  const edges = [];
  for (let y = 0; y < H; y += 4) {
    const cols = [px(0, y), px(1, y), px(W - 2, y), px(W - 1, y)];
    edges.push([0, 1, 2].map((k) => Math.round(cols.reduce((sum, c) => sum + c[k], 0) / 4)));
  }

  const left = Math.floor(frac.towerL * W) - 1;
  const right = Math.ceil(frac.towerR * W) + 1;
  const bottom = Math.floor(frac.horizon * H) - 2;
  let diff = 0;
  let count = 0;
  for (let y = 1; y < bottom; y++) {
    for (let x = 1; x < W; x++) {
      if (x >= left && x <= right) continue;
      const p = px(x, y);
      const west = px(x - 1, y);
      const north = px(x, y - 1);
      for (let k = 0; k < 3; k++) diff += Math.abs(p[k] - west[k]) + Math.abs(p[k] - north[k]);
      count += 6;
    }
  }
  return { edges, skyClean: count > 0 && diff / count < 4 };
}

/* ------------------------------------------------------------------- film */

function film(root, plate, sample, frac, { gsap, ScrollTrigger }) {
  const $ = (selector) => root.querySelector(selector);
  const stage = $(".cine__stage");
  const intro = $(".cine__intro");
  const camera = $(".cine__camera");
  const haze = $(".cine__haze");
  const fogBack = $(".cine__fog--back");
  const fogFront = $(".cine__fog--front");
  const ren = $(".cine__ren");
  const ground = $(".cine__ground");
  const cue = $(".cine__cue");
  const title = $(".cine__title");
  // The copy's own blocks — eyebrow, headline, tagline, buttons — rise in turn.
  const titleItems = [...(title?.firstElementChild?.children ?? [])];
  const header = document.getElementById("site-header");
  const clouds = [...root.querySelectorAll("[data-cloud]")]
    .filter((el) => CLOUDS[el.dataset.cloud])
    .map((el) => ({ el, ...CLOUDS[el.dataset.cloud] }));
  const focusEnd = parseFloat(root.dataset.focusEnd) || 0.86;

  // Sky drift: only where there is room for it to read, and only when this
  // photo really has clean sky where the mask expects it.
  let sky = null;
  if (sample.skyClean && innerWidth >= 768) {
    const holder = Object.assign(document.createElement("div"), { className: "cine__sky" });
    holder.setAttribute("aria-hidden", "true");
    const img = Object.assign(new Image(), { alt: "", decoding: "async", src: plate.currentSrc || plate.src });
    holder.append(img);
    camera.append(holder);
    sky = { holder, img };
  }

  /* Layout — rebuilt on every ScrollTrigger refresh (resize, orientation). */
  const L = {};
  function measure() {
    const vw = stage.clientWidth;
    const vh = stage.clientHeight;
    const towerWidth = frac.towerR - frac.towerL;

    // Landscape: the render covers the width (capped on ultra-wide screens,
    // where the sampled edge colours carry the sky on). Portrait: a closer
    // camera, the tower filling most of the frame — a phone gets its own
    // framing rather than a shrunken desktop shot.
    const cover = Math.min(vw, vh * 2.1);
    const fill = gsap.utils.clamp(0.5, 0.92, gsap.utils.mapRange(1, 0.46, 0.5, 0.92, vw / vh));
    const w = vw < vh ? Math.max(cover, (vw * fill) / towerWidth) : cover;
    const h = (w * plate.naturalHeight) / plate.naturalWidth;
    const headerHeight = header ? header.offsetHeight : 0;

    Object.assign(L, {
      vw,
      vh,
      w,
      h,
      x0: vw / 2 - ((frac.towerL + frac.towerR) / 2) * w,
      // First frame: the crown clear of the header, with sky above it.
      yStart: Math.max(0, headerHeight + vh * 0.06 - frac.crown * h),
      // Last frame: the entrance a little above centre, with at most a sliver
      // of dark ground showing past the bottom of the render.
      yEnd: Math.max(vh - h - vh * 0.12, vh * 0.42 - focusEnd * h),
    });

    camera.style.width = `${w}px`;
    for (const c of clouds) {
      c.w = c.el.offsetWidth;
      c.h = c.el.offsetHeight;
    }

    const above = L.yStart + vh;
    root.style.setProperty("--cine-above", `${above}px`);
    root.style.setProperty("--cine-below", `${vh}px`);
    if (sample.edges) {
      const rgb = (c) => `rgb(${c.join(" ")})`;
      const last = sample.edges.length - 1;
      const stops = sample.edges.map((c, i) => `${rgb(c)} ${(above + (i / last) * h).toFixed(1)}px`);
      root.style.setProperty(
        "--cine-edges",
        `linear-gradient(${rgb(sample.edges[0])} ${above}px, ${stops.join(", ")}, ${rgb(sample.edges[last])})`,
      );
    }
  }

  /* One frame of the film, for the current shot.t. */
  const shot = { t: 0 };
  function render() {
    const { t } = shot;
    const { vw, vh, h } = L;
    const cx = vw / 2;
    const cy = vh / 2;

    // Camera. y0 is where the top of the render sits at zoom 1; the zoom is
    // then taken about the centre of the frame.
    const y0 = L.yStart + (L.yEnd - L.yStart) * descent(t);
    const s = keyframed(ZOOM, t);
    camera.style.transform =
      `translate3d(${(cx - s * (cx - L.x0)).toFixed(2)}px, ${(cy - s * (cy - y0)).toFixed(2)}px, 0) scale(${s.toFixed(4)})`;
    if (sky) sky.img.style.transform = `translate3d(0, ${((L.yStart - y0) * SKY_DRIFT).toFixed(2)}px, 0)`;

    // Title. It hangs in the sky, so it rides up with the sky copy as the
    // camera starts down, and is gone before the first clouds rise.
    if (title) {
      const hold = 1 - smooth(...SCENE.title, t);
      show(title, hold);
      if (hold) title.style.transform = `translate3d(0, ${((y0 - L.yStart) * (1 - SKY_DRIFT)).toFixed(2)}px, 0)`;
    }

    // Clouds. Each floats at a height in the render, so it rises into frame
    // from below and leaves above as the camera passes its altitude — nearer
    // ones faster, and swelling as they brush the lens.
    const altitude = cy - y0;
    const clearing = smooth(...SCENE.clearing, t);
    // Opens as the word surfaces, closes again as it recedes.
    const parting = smooth(0.6, 0.67, t) * (1 - smooth(...SCENE.recede, t));
    for (const c of clouds) {
      const o = smooth(...c.in, t) * (1 - smooth(...c.out, t)) * (1 - (c.yield || 0) * parting);
      show(c.el, o);
      if (!o) continue;
      const y = (c.alt * h - altitude) * c.depth;
      const k = c.scale * (1 + c.grow * clamp01(0.5 - y / vh));
      const x = ((c.x + c.part * (clearing + (c.yield ? 0.45 * parting : 0))) / 100) * vw;
      c.el.style.transform =
        `translate3d(${(x - c.w / 2).toFixed(1)}px, ${(y - c.h / 2).toFixed(1)}px, 0) ` +
        `scale(${(c.flip ? -k : k).toFixed(4)}, ${k.toFixed(4)})`;
    }

    // Atmosphere. The front fog is the curtain the wordmark is seen through:
    // it closes, thins to a trace so REN holds crisp, closes again, clears.
    show(haze, envelope(t, SCENE.haze) * 0.85);
    show(fogBack, envelope(t, SCENE.fogBack));
    show(fogFront, clamp01(
      0.97 * smooth(0.52, 0.6, t) - 0.88 * smooth(0.6, 0.68, t) +
      0.78 * smooth(0.72, 0.78, t) - 0.87 * smooth(0.78, 0.88, t),
    ));
    fogFront.style.transform = `scale(${(1 + 0.08 * smooth(0.5, 0.9, t)).toFixed(4)})`;

    // REN — surfaces sharp and settles from slightly oversized, then sinks
    // back into the fog. It drifts up a touch with the camera, so it belongs
    // to the scene rather than sitting on the glass.
    const reveal = smooth(...SCENE.reveal, t);
    const recede = smooth(...SCENE.recede, t);
    const presence = smooth(0.575, 0.66, t) * (1 - recede);
    show(ren, presence);
    if (presence) {
      const blur = 12 * (1 - reveal) + 10 * recede;
      ren.style.filter = blur > 0.1 ? `blur(${blur.toFixed(2)}px)` : "none";
      ren.style.transform =
        `translate3d(0, ${((0.68 - t) * vh * 0.08).toFixed(1)}px, 0) scale(${(1.1 - 0.1 * reveal - 0.03 * recede).toFixed(4)})`;
    }

    show(ground, smooth(...SCENE.ground, t));
    show(cue, 1 - smooth(...SCENE.cue, t));
  }

  const tween = gsap.to(shot, {
    t: 1,
    ease: "none",
    onUpdate: render,
    scrollTrigger: {
      // The track rather than #hero: the steps that follow it belong to the
      // section, not to the shot.
      trigger: $(".cine__track") ?? root,
      start: "top top",
      end: "bottom bottom",
      // Smoothing is the camera operator's hand: generous with a wheel,
      // tighter under a finger so touch doesn't feel like it lags.
      scrub: matchMedia("(pointer: coarse)").matches ? 0.6 : 1.1,
      onRefresh: () => {
        measure();
        render();
      },
      onToggle: (self) => root.classList.toggle("is-active", self.isActive),
    },
  });
  measure();
  render();

  // Entrance: the render settles in — barely a scale, mostly light — and the
  // copy rises into the sky over it once the picture is there.
  gsap.set(intro, { transformOrigin: "50% 12%" });
  const enter = gsap.timeline()
    .fromTo(intro, { autoAlpha: 0 }, { autoAlpha: 1, duration: 1.6, ease: "power2.out" })
    .fromTo(intro, { scale: 1.045 }, { scale: 1, duration: 2.8, ease: "power3.out" }, 0);
  if (titleItems.length) {
    enter.fromTo(titleItems, { y: 24, autoAlpha: 0 },
      { y: 0, autoAlpha: 1, duration: 1.2, ease: "power3.out", stagger: 0.09 }, 0.55);
  }

  return () => {
    enter.kill();
    tween.scrollTrigger?.kill();
    tween.kill();
    sky?.holder.remove();
    root.classList.remove("is-active");
    for (const prop of ["--cine-above", "--cine-below", "--cine-edges"]) root.style.removeProperty(prop);
    gsap.set([intro, camera, haze, fogBack, fogFront, ren, ground, cue, title, ...titleItems, ...clouds.map((c) => c.el)].filter(Boolean), {
      clearProps: "all",
    });
  };
}

/* ------------------------------------------------------------------ entry */

export async function initCinematicHero(root, gsapApi) {
  if (!root) return;
  const plate = root.querySelector(".cine__plate");

  try {
    await imageReady(plate);
  } catch {
    // No render to film: fall back to the still hero the CSS renders without
    // .cine-js — the title over the stage, the steps after it.
    document.documentElement.classList.remove("cine-js");
    return;
  }
  root.classList.add("is-live");

  const css = getComputedStyle(root);
  const pct = (name, fallback) => (parseFloat(css.getPropertyValue(name)) || fallback) / 100;
  const frac = {
    towerL: pct("--cine-tower-l", 26),
    towerR: pct("--cine-tower-r", 76),
    crown: pct("--cine-crown", 6),
    horizon: pct("--cine-horizon", 44),
  };
  const sample = sampleRender(plate, frac);

  // Reduced motion keeps the still hero the CSS already shows; flipping the
  // preference while the page is open builds or tears down the film live.
  gsapApi.gsap.matchMedia().add("(prefers-reduced-motion: no-preference)", () =>
    film(root, plate, sample, frac, gsapApi),
  );
}
