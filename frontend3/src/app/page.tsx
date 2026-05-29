"use client";

import {
  motion,
  AnimatePresence,
  useInView,
  useScroll,
  useTransform,
  useReducedMotion,
  MotionValue,
} from "framer-motion";
import Image from "next/image";
import { useRef, useState, useEffect } from "react";

/* Detect mobile once on mount — disables parallax on small screens */
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check, { passive: true });
    return () => window.removeEventListener("resize", check);
  }, []);
  return isMobile;
}
import {
  Rocket,
  ArrowRight,
  FileText,
  Cpu,
  Layers,
  ShieldCheck,
  Settings,
  Battery,
  Plane,
  Car,
  Speaker,
  Timer,
  Wrench,
  Factory,
  Zap,
  GraduationCap,
  Award,
  Brain,
  Briefcase,
  Code,
  BarChart3,
  X,
} from "lucide-react";

/* ──────────────────────────────────────────────
   Reusable fade-up wrapper — triggers on scroll
   ────────────────────────────────────────────── */
function FadeUp({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef(null);
  // Use a smaller margin on mobile (no negative margin) to avoid iOS viewport quirks
  const isInView = useInView(ref, { once: true, margin: "0px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.4, 0.25, 1] }}
      className={className}
      style={{ willChange: "opacity, transform" }}
    >
      {children}
    </motion.div>
  );
}

/* ──────────────────────────────────────────────
   Parallax floating orb — moves on scroll
   Disabled on reduced-motion / low-power iOS
   ────────────────────────────────────────────── */
function FloatingOrb({
  scrollY,
  speed,
  color,
  size,
  blur,
  left,
  top,
  opacity = 0.06,
}: {
  scrollY: MotionValue<number>;
  speed: number;
  color: string;
  size: number;
  blur: number;
  left: string;
  top: string;
  opacity?: number;
}) {
  const prefersReduced = useReducedMotion();
  // Clamp blur to 80px max — larger values tank Safari GPU
  const safeBr = Math.min(blur, 80);
  const y = useTransform(scrollY, [0, 5000], [0, prefersReduced ? 0 : speed]);

  return (
    <motion.div
      style={{
        y,
        left,
        top,
        width: size,
        height: size,
        background: color,
        opacity,
        filter: `blur(${safeBr}px)`,
        WebkitFilter: `blur(${safeBr}px)`,
        willChange: "transform",
      }}
      className="parallax-layer pointer-events-none absolute rounded-full"
    />
  );
}

/* ──────────────────────────────────────────────
   Parallax geometric shapes — rings / diamonds
   ────────────────────────────────────────────── */
function FloatingRing({
  scrollY,
  speed,
  color,
  size,
  left,
  top,
  borderWidth = 1,
  rotate = 0,
}: {
  scrollY: MotionValue<number>;
  speed: number;
  color: string;
  size: number;
  left: string;
  top: string;
  borderWidth?: number;
  rotate?: number;
}) {
  const prefersReduced = useReducedMotion();
  const y = useTransform(scrollY, [0, 5000], [0, prefersReduced ? 0 : speed]);
  const r = useTransform(scrollY, [0, 5000], [rotate, prefersReduced ? rotate : rotate + speed * 0.05]);

  return (
    <motion.div
      style={{
        y,
        rotate: r,
        left,
        top,
        width: size,
        height: size,
        borderColor: color,
        borderWidth,
        willChange: "transform",
      }}
      className="parallax-layer pointer-events-none absolute rounded-full border-solid opacity-[0.12]"
    />
  );
}

function FloatingDiamond({
  scrollY,
  speed,
  color,
  size,
  left,
  top,
}: {
  scrollY: MotionValue<number>;
  speed: number;
  color: string;
  size: number;
  left: string;
  top: string;
}) {
  const prefersReduced = useReducedMotion();
  const y = useTransform(scrollY, [0, 5000], [0, prefersReduced ? 0 : speed]);
  const r = useTransform(scrollY, [0, 5000], [45, prefersReduced ? 45 : 45 + speed * 0.03]);

  return (
    <motion.div
      style={{
        y,
        rotate: r,
        left,
        top,
        width: size,
        height: size,
        borderColor: color,
        willChange: "transform",
      }}
      className="parallax-layer pointer-events-none absolute border border-solid opacity-[0.1] rounded-sm"
    />
  );
}

/* ──────────────────────────────────────────────
   Horizontal scan-line (moves sideways on scroll)
   ────────────────────────────────────────────── */
function ScanLine({
  scrollY,
  speed,
  color,
  top,
  width = "40%",
}: {
  scrollY: MotionValue<number>;
  speed: number;
  color: string;
  top: string;
  width?: string;
}) {
  const prefersReduced = useReducedMotion();
  const x = useTransform(scrollY, [0, 5000], ["-20%", prefersReduced ? "-20%" : `${speed}%`]);

  return (
    <motion.div
      style={{
        x,
        top,
        width,
        background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
        willChange: "transform",
      }}
      className="parallax-layer pointer-events-none absolute left-0 h-px opacity-20"
    />
  );
}

/* ══════════════════════════════════════════════
   SECTION 1 — Hero
   ══════════════════════════════════════════════ */
function HeroSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section className="relative min-h-screen flex items-center justify-center hero-mesh overflow-hidden w-full">
      {/* Parallax floating elements — hidden on mobile for performance */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-200} color="#826015" size={500} blur={80} left="15%" top="10%" opacity={0.06} />
          <FloatingOrb scrollY={scrollY} speed={-300} color="#0E7490" size={400} blur={80} left="80%" top="5%" opacity={0.05} />
          <FloatingRing scrollY={scrollY} speed={-180} color="#0E7490" size={200} left="85%" top="25%" borderWidth={1} />
          <ScanLine scrollY={scrollY} speed={40} color="#0E7490" top="30%" />
        </div>
      )}

      {/* Subtle grid overlay removed */}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-5xl px-6 py-32 text-center">
        {/* Pill badge */}
        <FadeUp>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full bg-[#514733]/60 px-5 py-2.5 text-sm font-medium text-[#EAC97C] ring-1 ring-[#0E7490]/30 backdrop-blur-sm">
            <Rocket className="h-4 w-4" />
            Proudly contributing to AI INDIA Mission
          </div>
        </FadeUp>

        {/* Main heading */}
        <FadeUp delay={0.1}>
          <h1 className="font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-7xl lg:text-8xl">
            <span className="text-gradient-gold">
              Automated Electronic
              <br />
              Design Initiative
            </span>
            <span className="mt-3 block text-2xl font-semibold tracking-[0.25em] text-[#0E7490] sm:text-3xl md:text-4xl">
              AEDI
            </span>
          </h1>
        </FadeUp>

        {/* Subtitle */}
        <FadeUp delay={0.2}>
          <p className="mx-auto mt-8 max-w-2xl text-base leading-relaxed text-[#B7AA91] sm:text-lg md:text-xl">
            Empowering embedded electronics ecosystem through High Performance
            Computing. AEDI engineers successfully tested the hypothesis to
            commit towards a product focused, generative AI approach to synthesize
            and deliver physically feasible, comprehensive, embedded system designs.
          </p>
        </FadeUp>

        {/* CTA Buttons */}
        <FadeUp delay={0.3}>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="#vision"
              className="group relative inline-flex items-center gap-2 rounded-xl bg-[#826015] px-8 py-4 text-base font-semibold text-[#1E1B1B] transition-all duration-300 hover:bg-[#8F7E5E] hover:shadow-[0_0_30px_rgba(118,185,0,0.2)]"
            >
              Explore the Initiative
              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </a>
            <a
              href="/demo"
              className="glass inline-flex items-center gap-2 rounded-xl px-8 py-4 text-base font-semibold text-[#EAC97C] transition-all duration-300 hover:bg-[#514733]/40 hover:shadow-[0_0_20px_rgba(14,116,144,0.2)]"
            >
              <FileText className="h-4 w-4" />
              Concept Demo
            </a>
          </div>
        </FadeUp>

        {/* Partner logos badge — CSS float animation (no JS loop) */}
        <FadeUp delay={0.5}>
          <div className="mt-20 flex flex-col items-center justify-center gap-4 float-anim">
            <span className="text-2xl font-medium text-[#EAC97C]">In association with</span>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-8">
              {/* IIT Delhi logo */}
              <div className="flex flex-col items-center gap-2">
                <Image
                  src="/images/iitd_logo.png"
                  alt="IIT Delhi"
                  width={144}
                  height={144}
                  className="h-28 sm:h-36 w-auto object-contain"
                  priority
                />
                <span className="text-xs font-medium tracking-wide text-[#B7AA91]/70">IIT Delhi</span>
              </div>
              {/* NVIDIA logo */}
              <div className="flex flex-col items-center gap-2">
                <Image
                  src="/images/nvidia.png"
                  alt="NVIDIA Inception"
                  width={144}
                  height={144}
                  className="h-28 sm:h-36 w-auto object-contain"
                  priority
                />
                <span className="text-xs font-medium tracking-wide text-[#B7AA91]/70">NVIDIA Inception</span>
              </div>
            </div>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 2 — The Vision (Video Background)
   ══════════════════════════════════════════════ */
function VisionSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section
      id="vision"
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden section-lazy"
    >
      {/* VIDEO PLACEHOLDER — Replace src with your .mp4 URL */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 h-full w-full object-cover opacity-20"
      // src="/your-video.mp4"
      />

      {/* Subtle top/bottom fade for smooth transitions */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#1E1B1B]/60 via-transparent to-[#1E1B1B]/60" />

      {/* Parallax elements — desktop only */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-400} color="#0E7490" size={500} blur={80} left="60%" top="10%" opacity={0.07} />
          <FloatingOrb scrollY={scrollY} speed={-250} color="#826015" size={400} blur={80} left="10%" top="30%" opacity={0.05} />
          <FloatingRing scrollY={scrollY} speed={-200} color="#EAC97C" size={160} left="5%" top="20%" />
          <ScanLine scrollY={scrollY} speed={60} color="#0E7490" top="45%" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-4xl px-6 py-32 text-center">
        <FadeUp>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#0E7490] ring-1 ring-[#0E7490]/20">
            The Vision
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
            <span className="text-[#EAC97C]">Automation in Electronic Systems Design </span>
            <br />
            <span className="text-[#EAC97C]">is the{" "}</span>
            <span className="text-[#ffffff]">Next Big Thing!</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.2}>
          <div className="mx-auto my-8 h-px w-24 bg-gradient-to-r from-transparent via-[#0E7490] to-transparent" />
        </FadeUp>

        <FadeUp delay={0.25}>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed text-[#C8BAA6] sm:text-xl md:text-2xl">
            As artificial intelligence advances and becomes more deterministic,
            AI for Electronic Design Automation (EDA) is not just an evolution — it is{" "}
            <span className="font-semibold text-[#0E7490]">inevitable!</span>
          </p>
        </FadeUp>

        <FadeUp delay={0.35}>
          <div className="mx-auto mt-16 max-w-2xl glass rounded-2xl px-8 py-10 text-center transition-all duration-300 hover:shadow-[0_0_20px_rgba(14,116,144,0.15)]">
            <div className="font-[family-name:var(--font-space-grotesk)] text-2xl font-bold text-[#0E7490] sm:text-3xl">
              LRM based EDA
            </div>
            <p className="mt-4 text-lg leading-relaxed text-[#C8BAA6] sm:text-2xl">
              AEDI&apos;s compute prowess to synthesize and deliver production ready embedded system designs, optimized for the end user.
            </p>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 3 — The Engine (AI Design Service)
   ══════════════════════════════════════════════ */
const workflowSteps = [
  {
    label: "Engineers & Reviewers",
    description: "Human experts define requirements and review outputs",
    accent: "#EAC97C",
    bgAccent: "#EAC97C",
    icon: Settings,
  },
  {
    label: "AI-Based Reasoning Layer",
    description: "Design-time assistant powered by large reasoning models",
    accent: "#0E7490",
    bgAccent: "#0E7490",
    icon: Brain,
  },
  {
    label: "Design Artifacts",
    description: "",
    accent: "#059669",
    bgAccent: "#059669",
    icon: Layers,
    bullets: [
      "Requirements Analysis & Validation",
      "Architecture Models & Hardware Design",
      "Code Skeletons",
      "In-loop Verification & Validation through Simulation",
      "Test Cases",
      "Safety Analyses",
    ],
  },
  {
    label: "Embedded Software",
    description: "Deterministic, verified firmware ready for deployment",
    accent: "#EAC97C",
    bgAccent: "#EAC97C",
    icon: Code,
  },
  {
    label: "Target Hardware / HIL",
    description: "Hardware-in-the-loop testing and final target deployment",
    accent: "#0E7490",
    bgAccent: "#0E7490",
    icon: Cpu,
  },
];

function EngineSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section id="engine" className="relative w-full overflow-hidden bg-[#1E1B1B] py-32 section-lazy">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#0E7490]/30 to-transparent" />

      {/* Parallax bg — desktop only */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-500} color="#059669" size={450} blur={80} left="75%" top="10%" opacity={0.05} />
          <FloatingOrb scrollY={scrollY} speed={-350} color="#826015" size={350} blur={80} left="5%" top="50%" opacity={0.05} />
          <FloatingRing scrollY={scrollY} speed={-400} color="#059669" size={180} left="90%" top="60%" />
          <ScanLine scrollY={scrollY} speed={50} color="#059669" top="25%" width="50%" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#059669] ring-1 ring-[#059669]/20">
              <Cpu className="h-3.5 w-3.5" />
              The Engine
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-[#EAC97C]">Automated Input Discovery to Embedded System Design</span>
            <br />
            <span className="text-[#0E7490]">AI-Driven Proprietary Design Solutions</span>
          </h2>
        </FadeUp>

        {/* Engine feature boxes — decreasing size left to right */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4 sm:gap-6">
          {[
            { text: "Generative AI with Large Reasoning Models", size: 400, mobileSize: 300, font: "text-lg sm:text-xl md:text-lg" },
            { text: "Causal Reasoning to Eliminate Hallucinations in Design", size: 250, mobileSize: 220, font: "text-sm sm:text-base md:text-sm" },
            { text: "Verifiable Simulation Engine", size: 160, mobileSize: 150, font: "text-xs sm:text-sm" },
            { text: "Physically Viable Designs", size: 130, mobileSize: 120, font: "text-[10px] sm:text-xs" },
          ].map((item, i) => (
            <FadeUp key={i} delay={0.15 + i * 0.08} className="w-full sm:w-auto flex justify-center">
              <div
                className="relative shrink-0 aspect-square"
                style={{ width: isMobile ? item.mobileSize : item.size, height: isMobile ? item.mobileSize : item.size }}
              >
                <img
                  src="/images/box.png"
                  alt=""
                  className="h-full w-full object-contain drop-shadow-xl"
                />
                <p className={`absolute inset-[20%] flex items-center justify-center text-center font-[family-name:var(--font-space-grotesk)] font-bold leading-snug text-[#EAC97C] ${item.font}`}>
                  {item.text}
                </p>
              </div>
            </FadeUp>
          ))}
        </div>

        {/* ── Workflow Diagram ── */}
        <div className="mt-24 w-full">
          <FadeUp>
            <h3 className="mb-12 text-center font-[family-name:var(--font-space-grotesk)] text-2xl font-bold text-[#EAC97C] sm:text-3xl">
              Design Workflow
            </h3>
          </FadeUp>

          {/* Desktop: horizontal flow */}
          <div className="hidden lg:block">
            <div className="flex items-start justify-center gap-0">
              {workflowSteps.map((step, i) => (
                <div key={step.label} className="flex items-start">
                  {/* Step card */}
                  <motion.div
                    initial={{ opacity: 0, scale: 0.85 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true, margin: "0px 0px -40px 0px" }}
                    transition={{ duration: 0.5, delay: i * 0.12, ease: "easeOut" }}
                    whileHover={{ y: -6, boxShadow: "0 16px 40px rgba(0,0,0,0.25)" }}
                    className="group relative w-48 flex-shrink-0 cursor-default rounded-2xl border border-white/10 bg-white/[0.06] p-5 backdrop-blur-sm transition-all duration-300 hover:border-white/20 hover:bg-white/[0.1]"
                  >
                    {/* Step number badge */}
                    <motion.div
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: i * 0.12 + 0.2, type: "spring", stiffness: 260, damping: 20 }}
                      className="absolute -top-3 -right-3 flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
                      style={{ backgroundColor: step.accent }}
                    >
                      {i + 1}
                    </motion.div>

                    {/* Icon */}
                    <div
                      className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-110"
                      style={{
                        backgroundColor: `${step.accent}18`,
                        border: `1px solid ${step.accent}35`,
                      }}
                    >
                      <step.icon className="h-7 w-7" style={{ color: step.accent }} />
                    </div>

                    {/* Label */}
                    <h4
                      className="text-center font-[family-name:var(--font-space-grotesk)] text-sm font-bold leading-tight"
                      style={{ color: step.accent }}
                    >
                      {step.label}
                    </h4>

                    {/* Description */}
                    {step.description && (
                      <p className="mt-2 text-center text-xs leading-relaxed text-[#B7AA91]">
                        {step.description}
                      </p>
                    )}

                    {/* Bullets for Design Artifacts */}
                    {step.bullets && (
                      <div className="mt-3 space-y-1.5">
                        {step.bullets.map((bullet) => (
                          <div key={bullet} className="flex items-start gap-1.5">
                            <span
                              className="mt-1.5 h-1 w-1 shrink-0 rounded-full"
                              style={{ backgroundColor: step.accent }}
                            />
                            <span className="text-[11px] leading-snug text-[#C8BAA6]">{bullet}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>

                  {/* Horizontal connector arrow */}
                  {i < workflowSteps.length - 1 && (
                    <div className="flex h-14 flex-shrink-0 items-center px-1 pt-8">
                      <motion.div
                        initial={{ scaleX: 0, opacity: 0 }}
                        whileInView={{ scaleX: 1, opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.4, delay: i * 0.12 + 0.3 }}
                        className="flex items-center"
                        style={{ transformOrigin: "left" }}
                      >
                        <div
                          className="h-px w-8"
                          style={{
                            background: `linear-gradient(to right, ${step.accent}80, ${workflowSteps[i + 1].accent}80)`,
                          }}
                        />
                        <div
                          className="h-0 w-0"
                          style={{
                            borderTop: "5px solid transparent",
                            borderBottom: "5px solid transparent",
                            borderLeft: `7px solid ${workflowSteps[i + 1].accent}`,
                          }}
                        />
                      </motion.div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Mobile / Tablet: vertical flow */}
          <div className="lg:hidden">
            <div className="mx-auto flex max-w-md flex-col items-center">
              {workflowSteps.map((step, i) => (
                <div key={step.label} className="flex w-full flex-col items-center">
                  <motion.div
                    initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true, margin: "0px 0px -40px 0px" }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                    className="group relative w-full rounded-2xl border border-white/10 bg-white/[0.06] p-5 backdrop-blur-sm transition-all duration-300 hover:border-white/20 hover:bg-white/[0.1]"
                  >
                    {/* Step number badge */}
                    <div
                      className="absolute -top-3 left-5 flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
                      style={{ backgroundColor: step.accent }}
                    >
                      {i + 1}
                    </div>

                    <div className="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-left gap-4">
                      <div
                        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
                        style={{
                          backgroundColor: `${step.accent}18`,
                          border: `1px solid ${step.accent}35`,
                        }}
                      >
                        <step.icon className="h-6 w-6" style={{ color: step.accent }} />
                      </div>
                      <div className="flex-1">
                        <h4
                          className="font-[family-name:var(--font-space-grotesk)] text-base font-bold"
                          style={{ color: step.accent }}
                        >
                          {step.label}
                        </h4>
                        {step.description && (
                          <p className="mt-1 text-sm text-[#B7AA91]">{step.description}</p>
                        )}
                      </div>
                    </div>

                    {step.bullets && (
                      <div className="mt-4 flex flex-col items-center sm:items-start gap-1.5 sm:pl-16">
                        {step.bullets.map((bullet) => (
                          <div key={bullet} className="flex items-start gap-2">
                            <span
                              className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                              style={{ backgroundColor: step.accent }}
                            />
                            <span className="text-sm leading-relaxed text-[#C8BAA6] text-center sm:text-left">{bullet}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>

                  {/* Vertical connector */}
                  {i < workflowSteps.length - 1 && (
                    <motion.div
                      initial={{ scaleY: 0, opacity: 0 }}
                      whileInView={{ scaleY: 1, opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.3, delay: i * 0.1 + 0.2 }}
                      className="flex flex-col items-center py-1"
                      style={{ transformOrigin: "top" }}
                    >
                      <div
                        className="h-8 w-px"
                        style={{
                          background: `linear-gradient(to bottom, ${step.accent}60, ${workflowSteps[i + 1].accent}60)`,
                        }}
                      />
                      <div
                        className="h-0 w-0"
                        style={{
                          borderLeft: "5px solid transparent",
                          borderRight: "5px solid transparent",
                          borderTop: `7px solid ${workflowSteps[i + 1].accent}`,
                        }}
                      />
                    </motion.div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 4 — The Scope (Applications)
   ══════════════════════════════════════════════ */
const scopeItems = [
  {
    icon: Battery,
    image: "/images/BMS.png",
    title: "Battery & Mobility Systems",
    description:
      "AEDI automates mechanical, thermal, and electronic (BMS) battery designs for portable packs, two-wheelers, and three-wheelers.",
    accent: "#059669",
  },
  {
    icon: Plane,
    image: "/images/DroneCircuit.jpg",
    title: "Aerospace & Defence",
    description:
      "Our designs power drones, night vision devices, and radar systems.",
    accent: "#0E7490",
  },
  {
    icon: Car,
    image: "/images/automotive.png",
    title: "Automotive Integration",
    description:
      "We build optimized simple as well as complex controllers for various interdependent automotive applications.",
    accent: "#EAC97C",
  },
  {
    icon: Speaker,
    image: "/images/ESS.png",
    title: "Industrial & Consumer Power Electronics",
    description:
      "AEDI solutions to automate telecom power, home power storage systems, renewable energy systems, ESS. . .",
    accent: "#059669",
  },
];

function ScopeSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section id="scope" className="relative w-full overflow-hidden py-32 section-lazy">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#0E7490]/30 to-transparent" />

      {/* Parallax bg — desktop only */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-650} color="#0E7490" size={500} blur={80} left="0%" top="20%" opacity={0.06} />
          <FloatingOrb scrollY={scrollY} speed={-500} color="#826015" size={350} blur={80} left="70%" top="50%" opacity={0.04} />
          <FloatingRing scrollY={scrollY} speed={-550} color="#EAC97C" size={200} left="80%" top="20%" />
          <ScanLine scrollY={scrollY} speed={70} color="#0E7490" top="15%" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#0E7490] ring-1 ring-[#0E7490]/20">
              The Scope
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-gradient-gold">One Platform.</span>{" "}
            <span className="text-[#0E7490]">Multiple</span>{" "}
            <span className="text-gradient-gold">Applications.</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-3xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            AEDI is a dynamic functional model generating comprehensive embedded system designs for a range of applications.
          </p>
        </FadeUp>

        <div className="mt-16 w-full space-y-6">
          {scopeItems.map((item, i) => (
            <FadeUp key={item.title} delay={0.1 + i * 0.08}>
              <div
                className={`glass flex flex-col items-center text-center gap-6 rounded-2xl p-8 transition-all duration-300 hover:shadow-[0_0_25px_rgba(14,116,144,0.1)] md:flex-row ${i % 2 !== 0 ? "md:flex-row-reverse md:text-right" : "md:text-left"
                  }`}
              >
                <div
                  className="shrink-0 rounded-2xl p-5"
                  style={{
                    backgroundColor: `${item.accent}12`,
                    border: `1px solid ${item.accent}30`,
                  }}
                >
                  <item.icon
                    className="h-8 w-8"
                    style={{ color: item.accent }}
                  />
                </div>

                <div className="flex-1">
                  <h3 className="font-[family-name:var(--font-space-grotesk)] text-xl font-bold text-[#EAC97C] sm:text-2xl">
                    {item.title}
                  </h3>
                  <p className="mt-2 leading-relaxed text-[#B7AA91]">
                    {item.description}
                  </p>
                </div>

                <div className="shrink-0 rounded-xl w-full flex justify-center mt-4 md:mt-0 md:w-auto md:block">
                  <Image
                    src={item.image}
                    alt={item.title}
                    width={208}
                    height={144}
                    className="h-48 w-full rounded-xl object-contain md:h-36 md:w-52"
                    loading="lazy"
                  />
                </div>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 5 — The Impact (Value Proposition)
   ══════════════════════════════════════════════ */
const impactStats = [
  {
    icon: Timer,
    stat: ">60%",
    title: "Massive Time Savings",
    description:
      "Experience greater than 60% reduction in design and iteration time.",
    accent: "#0E7490",
  },
  {
    icon: Wrench,
    stat: "~70%",
    title: "Development Cost Reduction",
    description:
      "AEDI drives up to 70% reduction in engineering efforts.",
    accent: "#EAC97C",
  },
  {
    icon: Factory,
    stat: "Optimized Designs",
    title: "Automated Customiztion",
    description:
      "Cost and time optimized, rule-based design developments with reduced judgment and bias errors.",
    accent: "#059669",
  },
  {
    icon: Zap,
    stat: "Dynamic Solutions",
    title: "3-5X logic path variants",
    description:
      "Multiple logic path concurrence based decisions to ensure Robustness, Reliability & Safety.",
    accent: "#0E7490",
  },
];

function ImpactSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section id="impact" className="relative w-full overflow-hidden bg-[#1E1B1B] py-32 section-lazy">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#0E7490]/30 to-transparent" />

      {/* Parallax bg — desktop only */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-800} color="#0E7490" size={600} blur={80} left="40%" top="0%" opacity={0.06} />
          <FloatingOrb scrollY={scrollY} speed={-650} color="#059669" size={400} blur={80} left="80%" top="40%" opacity={0.04} />
          <FloatingRing scrollY={scrollY} speed={-700} color="#0E7490" size={280} left="85%" top="15%" borderWidth={2} />
          <ScanLine scrollY={scrollY} speed={80} color="#0E7490" top="35%" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#059669] ring-1 ring-[#059669]/20">
              The Impact
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-[#EAC97C]">Redefining{" "}</span>
            <span className="text-[#0E7490]">Development</span>
            <span className="text-[#EAC97C]">{" "}Timelines</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-2xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            Our new-tech enabled system delivers best-in-class optimized system
            solutions, custom firmware, precise Gerber files, and an optimized Bill of Materials (BOM) for effective sourcing and seamless assembly.
          </p>
        </FadeUp>

        <div className="mt-16 flex w-full flex-col items-center gap-6 sm:grid sm:grid-cols-2 lg:grid-cols-4">
          {impactStats.map((item, i) => (
            <FadeUp key={item.title} delay={0.1 + i * 0.1} className="h-full w-full">
              <div className="glass-strong group rounded-2xl p-8 text-center transition-all duration-300 hover:shadow-[0_0_30px_rgba(14,116,144,0.12)] h-full flex flex-col">
                <div>
                  <div
                    className={`${item.stat.length > 5 ? "text-3xl sm:text-4xl" : "text-5xl sm:text-6xl"
                      } font-extrabold font-[family-name:var(--font-space-grotesk)]`}
                    style={{ color: item.accent }}
                  >
                    {item.stat}
                  </div>
                  <div className="mt-5">
                    <h3 className="font-[family-name:var(--font-space-grotesk)] text-lg font-bold text-[#EAC97C]">
                      {item.title}
                    </h3>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-[#B7AA91]">
                  {item.description}
                </p>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 6 — The Leadership (Team)
   ══════════════════════════════════════════════ */
const teamMembers = [
  {
    icon: Award,
    image: "/images/bhim_singh.jpg",
    name: "Prof. Bhim Singh",
    subtitle: "Dept. of Electrical Engineering, IIT Delhi",
    title: "Mentor, Shareholder",
    description: [
      "ANRF National Science Chair & Emeritus Professor. FNAE, FNA, FNASc, FASc, FTWAS, FIEEE, FIET, FIETE, FIE(I)",
      "Dean, Academics at IIT Delhi. August 2016 - August 2019.",
      "72 patents granted + 37 patents filed. Executed >90 sponsored consultancy projects. Published 1326 research papers in journals. Presented >1,841 papers across global conferences. Guided 134 Ph.D. dissertations and 183 M.E./M.Tech./M.S.(R) theses.",
      "Recipient of prestigious Rashtriya Vigyan Puraskar — Vigyan Shri by the President of India, 2024; Goyal Prize for Applied Sciences, Kurukshetra University, 2021-2022. Khosla National Research Award of IIT Roorkee, 2013. Shri Om Prakash Bhasin Award-2014 in the field of Engineering including Energy & Aerospace. Faculty Lifetime Research Award-2018 for overall research contribution at IIT Delhi.",
      "Co-authored a textbook on power quality: Power Quality Problems and Mitigation Techniques published by John Wiley & Sons Ltd. 2015.",
    ],
    accent: "#EAC97C",
  },
  {
    icon: GraduationCap,
    image: "/images/amit_gupta.png",
    name: "Prof. Amit Gupta",
    subtitle: "Dept. of Mechanical Engineering, IIT Delhi",
    title: "Mentor, Shareholder",
    description: [
      "Having joined as a faculty in May 2011, Prof. Gupta currently holds the Mehra Chair as a Professor in the Department of Mechanical Engineering at IIT Delhi.",
      "Prof. Gupta is also serving as Associate Dean (Infrastructure) in the institute since September 2024.",
      "Formerly, he held the NTPC Chair Professorship from January 2019 till December 2023. Prior to his current appointment, Prof. Gupta was a post-doctoral research fellow at the GM/UM Advanced Battery Coalition for Drivetrains (ABCD), University of Michigan (UM), Ann Arbor between 2009 and 2011.",
      "He received M.S. & Ph.D. at the University of Central Florida (UCF) in 2007 and 2009 respectively, and B.Tech. from IIT Delhi in 2004.",
      "Prof. Gupta was a recipient of the Mrs. Veena Arora Early Career Award given by IIT Delhi in February 2021.",
      "His broad research interests are in Lithium-based technologies, microfluidics and flapping wing aerodynamics.",
    ],
    accent: "#EAC97C",
  },
  {
    icon: Brain,
    image: "/images/santanu_chaudhury.png",
    name: "Prof. Santanu Chaudhury",
    subtitle: "Dept. of Electrical Engineering, IIT Delhi & IIT Jodhpur",
    title: "Master System Architect, Shareholder",
    description: [
      "Retired from Department of Electrical Engineering, IIT Delhi on 31 January 2026.",
      "Former Director, IIT Jodhpur and Director CSIR-Central Electronics Research Institute.",
      "Former Dean, Undergraduate Studies, IIT Delhi. Chair Professor positions at IIT Delhi.",
      "Awarded INSA medal for young scientists in 1993.",
      "Fellow of Indian National Academy of Engineers (INAE), The National Academy of Sciences (NASI) and International Association of Pattern Recognition (IAPR).",
      ">350 publications in reputed Journals and conferences.",
      "15 patents with technologies commercialized by global industries.",
      "Interests: Computer Vision, Artificial Intelligence, Digital Heritage, AR-VR & Multi-sensory media.",
      "B.Tech (1984) in Electronics and Electrical Communication Engg and Ph.D (1989) in Computer Science and Engg. from I.I.T, Kharagpur, India.",
    ],
    accent: "#EAC97C",
  },
  // {
  //   icon: Briefcase,
  //   image: "/images/chunchreek_singhvi.jpg",
  //   name: "Chunchreek Singhvi",
  //   title: "Shareholder",
  //   description: [
  //     "Identified the opportunity after 10+ years of hands-on industry experience in the space of embedded engineering management; chased the possibility and driver of the vision.",
  //     ">20 years as part of startup initiatives spanning across innovative technologies, venture capital and private equity. Delivered successful/failed/sustained operating startups to bloom into global businesses in 15 industries across 10 countries.",
  //     ">USD 700 Mn in business development, global tech JVs, technology adaptation, product development & operations experiences in India, USA, EU, Thailand & Hong Kong (China).",
  //     "USD 500 Mn VC-PE fund raising, investment & portfolio management experiences. Investment experience in technology platforms (Optical cables, Embedded Systems for Railways, Security, Defence, Road Transport), real estate, hotels, social impact, fashion.",
  //     "Smurfit, UC Dublin - Masters in Business; Bachelors in Law; B.A. Economics; Scholar at Eton & Reims.",
  //   ],
  //   accent: "#EAC97C",
  // },

  //add • Supported by a team of:
  //            Application specific Subject Matter Experts.
  //            Engineering Interns from the B.Tech programme of IIT Delhi.
  //            Professional Law, Accounting and Company Secretarial Firms for all Compliance & Documentation.
  //           
  {
    icon: Briefcase,
    image: "/images/man.png",
    name: "Chunchreek Singhvi",
    title: "Shareholder",
    description: [
      "Identified the opportunity after 10+ years of hands-on industry experience in the space of embedded engineering management; chased the possibility and driver of the vision.",
      ">20 years as part of startup initiatives spanning across innovative technologies, venture capital and private equity. Delivered successful/failed/sustained operating startups to bloom into global businesses in 15 industries across 10 countries.",
      ">USD 700 Mn in business development, global tech JVs, technology adaptation, product development & operations experiences in India, USA, EU, Thailand & Hong Kong (China).",
      "USD 500 Mn VC-PE fund raising, investment & portfolio management experiences. Investment experience in technology platforms (Optical cables, Embedded Systems for Railways, Security, Defence, Road Transport), real estate, hotels, social impact, fashion.",
      "Smurfit, UC Dublin - Masters in Business; Bachelors in Law; B.A. Economics; Scholar at Eton & Reims.",
    ],
    accent: "#EAC97C",
  },
  {
    icon: Code,
    image: "/images/duke.jpg",
    name: "Duke Jain",
    subtitle: "Dept. of Biochemical Engineering and Biotechnology, IIT Delhi",
    title: "Full-Stack Intern",
    description:
      "Pursuing B.Tech in Biochemical Engineering and Biotechnology at the Indian Institute of Technology Delhi.",
    accent: "#0E7490",
  },
  {
    icon: BarChart3,
    image: "/images/bhanu.jpg",
    name: "Bhanu",
    subtitle: "Dept. of Biochemical Engineering and Biotechnology, IIT Delhi",
    title: "Data Science Intern",
    description:
      "Pursuing studies in Biochemical Engineering and Biotechnology at the Indian Institute of Technology Delhi.",
    accent: "#bb8a1fff",
  },
];

function TeamCard({ member }: { member: (typeof teamMembers)[number] }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Card */}
      <div
        onClick={() => setOpen(true)}
        className="glass group flex h-full w-[90%] max-w-[400px] sm:w-full sm:max-w-none mx-auto cursor-pointer flex-col items-center rounded-2xl p-8 text-center transition-all duration-300 hover:shadow-[0_0_25px_rgba(14,116,144,0.1)]"
      >
        <div
          className="mb-6 flex h-24 w-24 items-center justify-center overflow-hidden rounded-full transition-all duration-300"
          style={{
            backgroundColor: `${member.accent}12`,
            boxShadow: `0 0 0 2px ${member.accent}30`,
          }}
        >
          {member.image ? (
            <Image
              src={member.image}
              alt={member.name}
              width={96}
              height={96}
              className="h-full w-full object-cover object-top"
              loading="lazy"
            />
          ) : (
            <member.icon
              className="h-8 w-8"
              style={{ color: member.accent }}
            />
          )}
        </div>

        <h3 className="font-[family-name:var(--font-space-grotesk)] text-lg font-bold text-[#EAC97C]">
          {member.name}
        </h3>
        {member.subtitle && (
          <p className="mt-1 text-xs leading-snug text-[#B7AA91]/70">
            {member.subtitle}
          </p>
        )}
        <div
          className="mt-1 text-xs font-semibold uppercase tracking-wider"
          style={{ color: member.accent }}
        >
          {member.title}
        </div>

        {/* Tap hint */}
        <p className="mt-4 text-xs text-[#B7AA91]/40">Click to read more</p>
      </div>

      {/* Modal overlay */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={() => setOpen(false)}
          >
            {/* Blurred backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

            {/* Modal content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 20 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              onClick={(e) => e.stopPropagation()}
              className="glass relative z-10 w-full max-w-[92vw] sm:max-w-[60vw] max-h-[85vh] overflow-y-auto rounded-2xl border border-[#8F7E5E]/20 p-6 sm:p-10"
            >
              {/* Close button */}
              <button
                onClick={() => setOpen(false)}
                className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-[#B7AA91]/60 transition-colors hover:bg-[#B7AA91]/10 hover:text-[#EAC97C]"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Header */}
              <div className="flex items-center gap-6">
                <div
                  className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full"
                  style={{
                    backgroundColor: `${member.accent}12`,
                    boxShadow: `0 0 0 2px ${member.accent}30`,
                  }}
                >
                  {member.image ? (
                    <Image
                      src={member.image}
                      alt={member.name}
                      width={80}
                      height={80}
                      className="h-full w-full object-cover object-top"
                      loading="lazy"
                    />
                  ) : (
                    <member.icon
                      className="h-8 w-8"
                      style={{ color: member.accent }}
                    />
                  )}
                </div>
                <div>
                  <h3 className="font-[family-name:var(--font-space-grotesk)] text-2xl font-bold text-[#EAC97C]">
                    {member.name}
                  </h3>
                  {member.subtitle && (
                    <p className="mt-1 text-sm text-[#B7AA91]/70">
                      {member.subtitle}
                    </p>
                  )}
                  <div
                    className="mt-1 text-sm font-semibold uppercase tracking-wider"
                    style={{ color: member.accent }}
                  >
                    {member.title}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="mt-8">
                {Array.isArray(member.description) ? (
                  <ul className="list-disc space-y-2 pl-5 text-base leading-relaxed text-[#B7AA91]">
                    {member.description.map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-base leading-relaxed text-[#B7AA91]">
                    {member.description}
                  </p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function LeadershipSection({ scrollY }: { scrollY: MotionValue<number> }) {
  const isMobile = useIsMobile();
  return (
    <section id="leadership" className="relative w-full overflow-hidden pt-32 pb-12 section-lazy">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#0E7490]/30 to-transparent" />

      {/* Parallax bg — desktop only */}
      {!isMobile && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb scrollY={scrollY} speed={-950} color="#0E7490" size={400} blur={80} left="70%" top="15%" opacity={0.05} />
          <FloatingOrb scrollY={scrollY} speed={-1050} color="#826015" size={350} blur={80} left="10%" top="50%" opacity={0.04} />
          <FloatingRing scrollY={scrollY} speed={-900} color="#EAC97C" size={160} left="85%" top="55%" />
          <ScanLine scrollY={scrollY} speed={90} color="#EAC97C" top="20%" width="30%" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex w-full flex-col items-center justify-center max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#EAC97C] ring-1 ring-[#8F7E5E]/20">
              Humans at AEDI
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-gradient-gold">The Minds Driving</span>{" "}
            <span className="text-[#0E7490]">India&apos;s</span>{" "}
            <span className="text-gradient-gold">Tech Sovereignty</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-2xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            Our initiative is guided by hands-on mentorship from distinguished
            leaders.
          </p>
        </FadeUp>

        <div className="mt-16 flex w-full flex-col items-center gap-6 sm:grid sm:grid-cols-2 lg:grid-cols-3">
          {teamMembers.map((member, i) =>
            member.image === "/images/man.png" ? (
              <FadeUp key={member.name} delay={0.1 + i * 0.1}>
                <div className="flex h-full items-center justify-center">
                  <Image
                    src="/images/man.png"
                    alt={member.name}
                    width={256}
                    height={256}
                    className="h-64 w-auto object-contain opacity-80"
                    loading="lazy"
                  />
                </div>
              </FadeUp>
            ) : (
              <FadeUp key={member.name} delay={0.1 + i * 0.1} className="flex w-full flex-col items-center sm:block">
                <TeamCard member={member} />
              </FadeUp>
            )
          )}
        </div>

      </div>
    </section>
  );
}

function ContactSection() {
  return (
    <section id="contact" className="relative w-full py-12 overflow-hidden">
      {/* ── Center content ── */}
      <div className="relative z-10 mx-auto w-full max-w-2xl px-6 text-center">
        {/* Email */}
        <a
          href="mailto:cs@chunchreek.com"
          className="inline-block text-lg font-semibold text-[#0E7490] transition-colors hover:text-[#0E7490]/80"
        >
          cs@chunchreek.com
        </a>

        {/* Promotion line */}
        <p className="mt-3 text-sm leading-relaxed text-[#B7AA91]/70">
          Automatic Electronic Design Initiative (AEDI) is promoted by{" "}
          <span className="text-[#EAC97C]/80 font-medium">
            Chunchreek Ventures India Private Limited (CVIL)
          </span>
        </p>

        {/* Address */}
        <p className="mt-3 text-xs leading-relaxed text-[#B7AA91]/60">
          📍 2C1B, Research and Innovation Park, Indian Institute of Technology (IIT) Delhi,<br />
          Hauz Khas, New Delhi – 110016, India
        </p>

        {/* Copyright */}
        <p className="mt-4 text-xs text-[#B7AA91]/50">
          Pictures Design and Content &copy; 2026 of CVIL
        </p>

        {/* CIN */}
        <p className="mt-1 text-xs text-[#B7AA91]/40">
          CIN: U70200HR2025PTC129523
        </p>

        {/* Social icons */}
        <div className="mt-6 flex items-center justify-center gap-5">
          {/* Instagram */}
          <a href="#" aria-label="Instagram" className="text-[#B7AA91]/50 transition-colors hover:text-[#EAC97C]">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" /></svg>
          </a>
          {/* Facebook */}
          <a href="#" aria-label="Facebook" className="text-[#B7AA91]/50 transition-colors hover:text-[#EAC97C]">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" /></svg>
          </a>
          {/* X / Twitter */}
          <a href="#" aria-label="X (Twitter)" className="text-[#B7AA91]/50 transition-colors hover:text-[#EAC97C]">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
          </a>
        </div>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   Page composition — scrollY shared across all
   ══════════════════════════════════════════════ */
export default function Home() {
  const { scrollY } = useScroll();

  return (
    <main className="relative w-full overflow-x-hidden">
      <HeroSection scrollY={scrollY} />
      <VisionSection scrollY={scrollY} />
      <EngineSection scrollY={scrollY} />
      <ScopeSection scrollY={scrollY} />
      <ImpactSection scrollY={scrollY} />
      <LeadershipSection scrollY={scrollY} />
      <ContactSection />
    </main>
  );
}
