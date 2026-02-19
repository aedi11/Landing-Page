"use client";

import {
  motion,
  useInView,
  useScroll,
  useTransform,
  MotionValue,
} from "framer-motion";
import { useRef, useState } from "react";
import {
  Rocket,
  ArrowRight,
  FileText,
  ChevronDown,
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
  ChevronUp,
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
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 }}
      transition={{ duration: 0.7, delay, ease: [0.25, 0.4, 0.25, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ──────────────────────────────────────────────
   Parallax floating orb — moves on scroll
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
  const y = useTransform(scrollY, [0, 5000], [0, speed]);

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
        filter: `blur(${blur}px)`,
      }}
      className="pointer-events-none absolute rounded-full"
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
  const y = useTransform(scrollY, [0, 5000], [0, speed]);
  const r = useTransform(scrollY, [0, 5000], [rotate, rotate + speed * 0.05]);

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
      }}
      className="pointer-events-none absolute rounded-full border-solid opacity-[0.12]"
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
  const y = useTransform(scrollY, [0, 5000], [0, speed]);
  const r = useTransform(scrollY, [0, 5000], [45, 45 + speed * 0.03]);

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
      }}
      className="pointer-events-none absolute border border-solid opacity-[0.1] rounded-sm"
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
  const x = useTransform(scrollY, [0, 5000], ["-20%", `${speed}%`]);

  return (
    <motion.div
      style={{
        x,
        top,
        width,
        background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
      }}
      className="pointer-events-none absolute left-0 h-px opacity-20"
    />
  );
}

/* ══════════════════════════════════════════════
   SECTION 1 — Hero
   ══════════════════════════════════════════════ */
function HeroSection({ scrollY }: { scrollY: MotionValue<number> }) {
  return (
    <section className="relative min-h-screen flex items-center justify-center hero-mesh overflow-hidden">
      {/* Parallax floating elements */}
      <div className="pointer-events-none absolute inset-0">
        {/* Warm gold orbs */}
        <FloatingOrb scrollY={scrollY} speed={-200} color="#826015" size={500} blur={120} left="15%" top="10%" opacity={0.06} />
        <FloatingOrb scrollY={scrollY} speed={-100} color="#EAC97C" size={300} blur={100} left="70%" top="60%" opacity={0.03} />
        {/* Cool contrast orbs — teal & emerald */}
        <FloatingOrb scrollY={scrollY} speed={-300} color="#0E7490" size={400} blur={130} left="80%" top="5%" opacity={0.05} />
        <FloatingOrb scrollY={scrollY} speed={-150} color="#059669" size={250} blur={100} left="5%" top="70%" opacity={0.04} />
        {/* Geometric shapes */}
        <FloatingRing scrollY={scrollY} speed={-180} color="#0E7490" size={200} left="85%" top="25%" borderWidth={1} />
        <FloatingRing scrollY={scrollY} speed={-80} color="#EAC97C" size={120} left="8%" top="30%" borderWidth={1} />
        <FloatingDiamond scrollY={scrollY} speed={-250} color="#059669" size={60} left="75%" top="70%" />
        <FloatingDiamond scrollY={scrollY} speed={-120} color="#826015" size={40} left="20%" top="55%" />
        {/* Scan lines */}
        <ScanLine scrollY={scrollY} speed={40} color="#0E7490" top="30%" />
        <ScanLine scrollY={scrollY} speed={25} color="#826015" top="70%" width="30%" />
      </div>

      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(14,116,144,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(234,201,124,0.2) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      <div className="relative z-10 mx-auto max-w-5xl px-6 py-32 text-center">
        {/* Pill badge */}
        <FadeUp>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full bg-[#514733]/60 px-5 py-2.5 text-sm font-medium text-[#EAC97C] ring-1 ring-[#0E7490]/30 backdrop-blur-sm">
            <Rocket className="h-4 w-4" />
            Proudly Contributing to AI INDIA Mission
          </div>
        </FadeUp>

        {/* Main heading */}
        <FadeUp delay={0.1}>
          <h1 className="font-[family-name:var(--font-space-grotesk)] text-5xl font-bold leading-[1.1] tracking-tight sm:text-6xl md:text-7xl lg:text-8xl">
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
            Empowering India&apos;s hardware ecosystem through high-powered
            computing. AEDI addresses the inefficiencies of traditional
            incumbents by offering sophisticated, AI-enabled capability stacks.
            We provide generic, simplified Electronic Design Automation (EDA)
            toolkits to accelerate innovation for developmental engineers.
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
              Demo
            </a>
          </div>
        </FadeUp>

        {/* Scroll indicator */}
        <FadeUp delay={0.5}>
          <motion.div
            className="mt-20 flex justify-center"
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <a
              href="#vision"
              className="flex flex-col items-center gap-1 text-xs font-medium uppercase tracking-widest text-[#0E7490] transition-colors hover:text-[#EAC97C]"
            >
              Scroll
              <ChevronDown className="h-4 w-4" />
            </a>
          </motion.div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════════
   SECTION 2 — The Vision (Video Background)
   ══════════════════════════════════════════════ */
function VisionSection({ scrollY }: { scrollY: MotionValue<number> }) {
  return (
    <section
      id="vision"
      className="relative flex min-h-screen items-center justify-center overflow-hidden"
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

      {/* Dark gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#1E1B1B] via-[#1E1B1B]/80 to-[#1E1B1B]" />

      {/* Parallax elements */}
      <div className="pointer-events-none absolute inset-0">
        <FloatingOrb scrollY={scrollY} speed={-400} color="#0E7490" size={500} blur={140} left="60%" top="10%" opacity={0.07} />
        <FloatingOrb scrollY={scrollY} speed={-250} color="#826015" size={400} blur={120} left="10%" top="30%" opacity={0.05} />
        <FloatingOrb scrollY={scrollY} speed={-350} color="#059669" size={300} blur={110} left="80%" top="60%" opacity={0.04} />
        <FloatingRing scrollY={scrollY} speed={-200} color="#EAC97C" size={160} left="5%" top="20%" />
        <FloatingRing scrollY={scrollY} speed={-300} color="#0E7490" size={240} left="90%" top="40%" borderWidth={2} />
        <FloatingDiamond scrollY={scrollY} speed={-180} color="#EAC97C" size={50} left="15%" top="75%" />
        <ScanLine scrollY={scrollY} speed={60} color="#0E7490" top="45%" />
      </div>

      <div className="relative z-10 mx-auto max-w-4xl px-6 py-32 text-center">
        <FadeUp>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#0E7490] ring-1 ring-[#0E7490]/20">
            The Vision
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="font-[family-name:var(--font-space-grotesk)] text-4xl font-bold leading-tight tracking-tight text-[#EAC97C] sm:text-5xl md:text-6xl lg:text-7xl">
            Automation in Electronic Design 
            <br />
            is the{" "}
            <span className="text-[#0E7490]">Next Big Thing.</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.2}>
          <div className="mx-auto my-8 h-px w-24 bg-gradient-to-r from-transparent via-[#0E7490] to-transparent" />
        </FadeUp>

        <FadeUp delay={0.25}>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed text-[#C8BAA6] sm:text-xl md:text-2xl">
            As artificial intelligence advances and becomes more deterministic,
            AI for Electronic Design Automation is not just an evolution — it is{" "}
            <span className="font-semibold text-[#0E7490]">inevitable</span>.
            We are building the engine for India&apos;s tech sovereignty.
          </p>
        </FadeUp>

        <FadeUp delay={0.35}>
          <div className="mt-16 flex flex-col justify-center gap-6 sm:flex-row">
            {[
              { value: "LRM-Based", label: "Design Approach", accent: "#0E7490" },
              { value: "EDA", label: "Next-Gen Toolkits", accent: "#059669" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="glass rounded-2xl px-6 py-8 transition-all duration-300 hover:shadow-[0_0_20px_rgba(14,116,144,0.15)]"
              >
                <div
                  className="font-[family-name:var(--font-space-grotesk)] text-2xl font-bold sm:text-3xl"
                  style={{ color: stat.accent }}
                >
                  {stat.value}
                </div>
                <div className="mt-2 text-sm font-medium text-[#8F7E5E]">
                  {stat.label}
                </div>
              </div>
            ))}
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
  const enginePoints = [
    {
      icon: Brain,
      text: "Uses large reasoning models as off-device, human-supervised design partners",
    },
    {
      icon: ShieldCheck,
      text: "Improve requirements quality, architecture design, verification depth, and safety documentation",
    },
    {
      icon: Layers,
      text: "Ensures logically verified, tested through simulation, deterministic embedded systems design",
    },
    {
      icon: Settings,
      text: "An LRM-augmented embedded system design toolchain",
    },
  ];

  return (
    <section id="engine" className="relative overflow-hidden bg-[#1E1B1B] py-32">
      {/* Parallax bg */}
      <div className="pointer-events-none absolute inset-0">
        <FloatingOrb scrollY={scrollY} speed={-500} color="#059669" size={450} blur={130} left="75%" top="10%" opacity={0.05} />
        <FloatingOrb scrollY={scrollY} speed={-350} color="#826015" size={350} blur={110} left="5%" top="50%" opacity={0.05} />
        <FloatingOrb scrollY={scrollY} speed={-600} color="#0E7490" size={300} blur={100} left="50%" top="70%" opacity={0.04} />
        <FloatingRing scrollY={scrollY} speed={-400} color="#059669" size={180} left="90%" top="60%" />
        <FloatingRing scrollY={scrollY} speed={-280} color="#826015" size={140} left="3%" top="15%" />
        <FloatingDiamond scrollY={scrollY} speed={-450} color="#0E7490" size={70} left="40%" top="5%" />
        <ScanLine scrollY={scrollY} speed={50} color="#059669" top="25%" width="50%" />
        <ScanLine scrollY={scrollY} speed={35} color="#826015" top="80%" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#059669] ring-1 ring-[#059669]/20">
            <Cpu className="h-3.5 w-3.5" />
            The Engine
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="font-[family-name:var(--font-space-grotesk)] text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-[#EAC97C]">From Requirements to Embedded System Design:</span>
            <br />
            <span className="text-[#0E7490]">An AI-Driven Design Service</span>
          </h2>
        </FadeUp>

        {/* Feature cards */}
        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {enginePoints.map((point, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.08 }}
              whileHover={{ y: -4, boxShadow: "0 12px 32px rgba(14,116,144,0.12)" }}
              className="group flex items-start gap-4 rounded-2xl border border-white/10 bg-white/[0.06] px-6 py-5 backdrop-blur-sm transition-colors duration-300 hover:border-white/20 hover:bg-white/[0.09]"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#0E7490]/15 ring-1 ring-[#0E7490]/25 transition-all duration-300 group-hover:bg-[#0E7490]/25">
                <point.icon className="h-5 w-5 text-[#0E7490]" />
              </div>
              <p className="text-sm leading-relaxed text-[#C8BAA6] md:text-base">{point.text}</p>
            </motion.div>
          ))}
        </div>

        {/* ── Workflow Diagram ── */}
        <div className="mt-24">
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
                    viewport={{ once: true, margin: "-40px" }}
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
                    viewport={{ once: true, margin: "-40px" }}
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

                    <div className="flex items-center gap-4">
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
                      <div className="mt-3 grid grid-cols-1 gap-1.5 pl-16 sm:grid-cols-2">
                        {step.bullets.map((bullet) => (
                          <div key={bullet} className="flex items-start gap-2">
                            <span
                              className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                              style={{ backgroundColor: step.accent }}
                            />
                            <span className="text-sm leading-relaxed text-[#C8BAA6]">{bullet}</span>
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
      "We automate mechanical, thermal, and electronic (BMS) battery designs for portable packs, two-wheelers, and three-wheelers.",
    accent: "#059669",
  },
  {
    icon: Plane,
    image: "/images/DroneCircuit.jpg",
    title: "Aerospace & Defence",
    description:
      "Our designs power drones, night vision powering solutions, and radar systems.",
    accent: "#0E7490",
  },
  {
    icon: Car,
    image: "/images/automotive.png",
    title: "Automotive Integration",
    description:
      "We build complex controllers for ECU load balancing and optimization, as well as electric vehicle chargers.",
    accent: "#EAC97C",
  },
  {
    icon: Speaker,
    image: "/images/ESS.png",
    title: "Consumer & Power Electronics",
    description:
      "Our solutions extend to motor controllers, home electronics, and portable audio devices.",
    accent: "#059669",
  },
];

function ScopeSection({ scrollY }: { scrollY: MotionValue<number> }) {
  return (
    <section id="scope" className="relative overflow-hidden py-32">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#0E7490]/40 to-transparent" />

      {/* Parallax bg */}
      <div className="pointer-events-none absolute inset-0">
        <FloatingOrb scrollY={scrollY} speed={-650} color="#0E7490" size={500} blur={140} left="0%" top="20%" opacity={0.06} />
        <FloatingOrb scrollY={scrollY} speed={-500} color="#826015" size={350} blur={120} left="70%" top="50%" opacity={0.04} />
        <FloatingOrb scrollY={scrollY} speed={-750} color="#059669" size={200} blur={90} left="90%" top="10%" opacity={0.05} />
        <FloatingRing scrollY={scrollY} speed={-550} color="#EAC97C" size={200} left="80%" top="20%" />
        <FloatingDiamond scrollY={scrollY} speed={-600} color="#0E7490" size={80} left="10%" top="60%" />
        <FloatingDiamond scrollY={scrollY} speed={-700} color="#059669" size={45} left="60%" top="80%" />
        <ScanLine scrollY={scrollY} speed={70} color="#0E7490" top="15%" />
        <ScanLine scrollY={scrollY} speed={45} color="#059669" top="65%" width="35%" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#0E7490] ring-1 ring-[#0E7490]/20">
              The Scope
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-[#EAC97C]">One Platform.</span>{" "}
            <span className="text-[#0E7490]">Infinite</span>{" "}
            <span className="text-[#EAC97C]">Embedded Systems.</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-3xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            AEDI acts as a comprehensive dynamic foundational model capable of
            generating a spectrum of application-level embedded system designs.
          </p>
        </FadeUp>

        <div className="mt-16 space-y-6">
          {scopeItems.map((item, i) => (
            <FadeUp key={item.title} delay={0.1 + i * 0.08}>
              <div
                className={`glass flex flex-col items-start gap-6 rounded-2xl p-8 transition-all duration-300 hover:shadow-[0_0_25px_rgba(14,116,144,0.1)] md:flex-row md:items-center ${
                  i % 2 !== 0 ? "md:flex-row-reverse md:text-right" : ""
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

                <div className="hidden shrink-0 rounded-xl lg:block">
                  <img
                    src={item.image}
                    alt={item.title}
                    className="h-36 w-52 rounded-xl object-contain"
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
      "Experience a greater than 60% reduction in design and iteration times.",
    accent: "#0E7490",
  },
  {
    icon: Wrench,
    stat: "~70%",
    title: "Engineering Optimization",
    description:
      "AEDI drives up to a 70% reduction in engineering efforts.",
    accent: "#EAC97C",
  },
  {
    icon: Factory,
    stat: "Seamless",
    title: "Seamless Manufacturing",
    description:
      "We deliver custom firmware, precise Gerber files, and an optimized Bill of Materials (BOM) for effective sourcing and seamless assembly.",
    accent: "#059669",
  },
  {
    icon: Zap,
    stat: "Dynamic",
    title: "Dynamic Design",
    description:
      "Achieve shorter time, cost-optimized, rule-based design developments with reduced judgment and bias errors.",
    accent: "#0E7490",
  },
];

function ImpactSection({ scrollY }: { scrollY: MotionValue<number> }) {
  return (
    <section id="impact" className="relative overflow-hidden bg-[#1E1B1B] py-32">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#059669]/40 to-transparent" />

      {/* Parallax bg */}
      <div className="pointer-events-none absolute inset-0">
        <FloatingOrb scrollY={scrollY} speed={-800} color="#0E7490" size={600} blur={160} left="40%" top="0%" opacity={0.06} />
        <FloatingOrb scrollY={scrollY} speed={-650} color="#059669" size={400} blur={120} left="80%" top="40%" opacity={0.04} />
        <FloatingOrb scrollY={scrollY} speed={-900} color="#826015" size={350} blur={110} left="5%" top="60%" opacity={0.05} />
        <FloatingRing scrollY={scrollY} speed={-700} color="#0E7490" size={280} left="85%" top="15%" borderWidth={2} />
        <FloatingRing scrollY={scrollY} speed={-550} color="#059669" size={100} left="10%" top="25%" />
        <FloatingDiamond scrollY={scrollY} speed={-850} color="#EAC97C" size={55} left="30%" top="80%" />
        <FloatingDiamond scrollY={scrollY} speed={-750} color="#0E7490" size={35} left="65%" top="10%" />
        <ScanLine scrollY={scrollY} speed={80} color="#0E7490" top="35%" />
        <ScanLine scrollY={scrollY} speed={55} color="#059669" top="75%" width="45%" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#059669] ring-1 ring-[#059669]/20">
              The Impact
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold tracking-tight text-[#EAC97C] sm:text-5xl md:text-6xl">
            Redefining{" "}
            <span className="text-[#0E7490]">Development</span>{" "}
            Timelines
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-2xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            Our new-tech enabled system delivers best-in-class optimized system
            solutions.
          </p>
        </FadeUp>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {impactStats.map((item, i) => (
            <FadeUp key={item.title} delay={0.1 + i * 0.1} className="h-full">
              <div className="glass-strong group rounded-2xl p-8 text-center transition-all duration-300 hover:shadow-[0_0_30px_rgba(14,116,144,0.12)] h-full flex flex-col justify-between">
                <div>
                  <div
                    className={`${
                      item.stat.length > 5 ? "text-3xl sm:text-4xl" : "text-5xl sm:text-6xl"
                    } font-extrabold font-[family-name:var(--font-space-grotesk)]`}
                    style={{ color: item.accent }}
                  >
                    {item.stat}
                  </div>
                  <div className="mt-5 flex items-center justify-center gap-2">
                    <item.icon
                      className="h-5 w-5"
                      style={{ color: item.accent }}
                    />
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
    title: "Mentor & Shareholder",
    description:
      "Emeritus Professor at IIT Delhi and recipient of the prestigious Rashtriya Vigyan Puraskar — Vigyan Shri by the President of India in 2024.",
    accent: "#EAC97C",
  },
  {
    icon: GraduationCap,
    image: "/images/amit_gupta.png",
    name: "Prof. Amit Gupta",
    subtitle: "Dept. of Mechanical Engineering, IIT Delhi",
    title: "Mentor",
    description:
      "Mehra Chair Professor in the Department of Mechanical Engineering at IIT Delhi, specializing in Lithium-based technologies.",
    accent: "#0E7490",
  },
  {
    icon: Brain,
    image: "/images/santanu_chaudhury.png",
    name: "Prof. Santanu Chaudhury",
    subtitle: "Dept. of Electrical Engineering, IIT Delhi & IIT Jodhpur",
    title: "Master System Architect",
    description:
      "Former Director of IIT Jodhpur, with expertise in Computer Vision and Artificial Intelligence.",
    accent: "#059669",
  },
  {
    icon: Briefcase,
    image: "/images/chunchreek_singhvi.jpg",
    name: "Chunchreek Singhvi",
    title: "Shareholder",
    description:
      "20+ years of hands-on industry experience in the space of embedded engineering management and startup initiatives spanning across innovative technologies, venture",
    accent: "#EAC97C",
  },
  {
    icon: Code,
    image: "/images/vipul.jpeg",
    name: "Vipul Lout",
    title: "Full-Stack Developer",
    description:
      "B.Tech graduate in Electrical Engineering from Indian Institute of Technology Delhi.",
    accent: "#0E7490",
  },
  {
    icon: BarChart3,
    image: "/images/Divyansh_kumar.png",
    name: "Divyansh Kumar",
    title: "Data Scientist Intern",
    description:
      "Pursuing B.Tech in Electrical Engineering from Indian Institute of Technology Delhi.",
    accent: "#bb8a1fff",
  },
];

function TeamCard({ member }: { member: (typeof teamMembers)[number] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className="glass group flex h-full cursor-pointer flex-col items-center rounded-2xl p-8 text-center transition-all duration-300 hover:shadow-[0_0_25px_rgba(14,116,144,0.1)]"
    >
      <div
        className="mb-6 flex h-24 w-24 items-center justify-center overflow-hidden rounded-full transition-all duration-300"
        style={{
          backgroundColor: `${member.accent}12`,
          boxShadow: `0 0 0 2px ${member.accent}30`,
        }}
      >
        {member.image ? (
          <img
            src={member.image}
            alt={member.name}
            className="h-full w-full object-cover"
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

      {/* Expandable description */}
      <motion.div
        initial={false}
        animate={{ height: expanded ? "auto" : 0, opacity: expanded ? 1 : 0 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="overflow-hidden"
      >
        <p className="mt-4 text-sm leading-relaxed text-[#B7AA91]">
          {member.description}
        </p>
      </motion.div>

      {/* Expand hint */}
      <ChevronUp
        className="mt-3 h-4 w-4 text-[#B7AA91]/50 transition-transform duration-300"
        style={{ transform: expanded ? "rotate(0deg)" : "rotate(180deg)" }}
      />
    </div>
  );
}

function LeadershipSection({ scrollY }: { scrollY: MotionValue<number> }) {
  return (
    <section id="leadership" className="relative overflow-hidden py-32">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-[#0E7490]/30 via-[#826015]/40 to-[#059669]/30" />

      {/* Parallax bg */}
      <div className="pointer-events-none absolute inset-0">
        <FloatingOrb scrollY={scrollY} speed={-950} color="#0E7490" size={400} blur={130} left="70%" top="15%" opacity={0.05} />
        <FloatingOrb scrollY={scrollY} speed={-1050} color="#826015" size={350} blur={110} left="10%" top="50%" opacity={0.04} />
        <FloatingOrb scrollY={scrollY} speed={-850} color="#059669" size={300} blur={100} left="50%" top="70%" opacity={0.04} />
        <FloatingRing scrollY={scrollY} speed={-900} color="#EAC97C" size={160} left="85%" top="55%" />
        <FloatingRing scrollY={scrollY} speed={-1000} color="#0E7490" size={220} left="5%" top="10%" borderWidth={2} />
        <FloatingDiamond scrollY={scrollY} speed={-1100} color="#059669" size={50} left="25%" top="80%" />
        <ScanLine scrollY={scrollY} speed={90} color="#EAC97C" top="20%" width="30%" />
        <ScanLine scrollY={scrollY} speed={65} color="#0E7490" top="85%" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6">
        <FadeUp>
          <div className="mb-6 text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#514733]/40 px-4 py-2 text-xs font-medium uppercase tracking-widest text-[#EAC97C] ring-1 ring-[#8F7E5E]/20">
              The Leadership
            </span>
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <h2 className="text-center font-[family-name:var(--font-space-grotesk)] text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            <span className="text-[#EAC97C]">The Minds Driving</span>{" "}
            <span className="text-[#0E7490]">India&apos;s</span>{" "}
            <span className="text-[#EAC97C]">Tech Sovereignty</span>
          </h2>
        </FadeUp>

        <FadeUp delay={0.15}>
          <p className="mx-auto mt-6 max-w-2xl text-center text-lg leading-relaxed text-[#B7AA91] md:text-xl">
            Our initiative is guided by hands-on mentorship from distinguished
            leaders.
          </p>
        </FadeUp>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {teamMembers.map((member, i) => (
            <FadeUp key={member.name} delay={0.1 + i * 0.1}>
              <TeamCard member={member} />
            </FadeUp>
          ))}
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
    <main>
      <HeroSection scrollY={scrollY} />
      <VisionSection scrollY={scrollY} />
      <EngineSection scrollY={scrollY} />
      <ScopeSection scrollY={scrollY} />
      <ImpactSection scrollY={scrollY} />
      <LeadershipSection scrollY={scrollY} />
    </main>
  );
}
