"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  Zap,
  Battery,
  Cpu,
  ChevronLeft,
  DollarSign,
  Gauge,
  Box,
  CheckCircle2,
  BrainCircuit,
} from "lucide-react";
import Link from "next/link";

/* ── Types ──────────────────────────────────────────────────────────────── */

interface ReasoningStep {
  step_number: number;
  title: string;
  description: string;
}

interface BOMComponent {
  item_number: number;
  component_name: string;
  description: string;
  quantity: number | string;
  specifications: string;
  estimated_unit_cost_usd?: string;
}

interface DesignChoice {
  topic: string;
  decision: string;
  rationale: string;
}

interface DesignVariant {
  variant_name: string;
  variant_description: string;
  project_summary: string;
  cell: Record<string, string | number>;
  pack_configuration: Record<string, string | number>;
  bms: Record<string, string | number | string[]>;
  cooling: Record<string, string | string[]>;
  design_choices: DesignChoice[];
  bom_table: BOMComponent[];
  total_estimated_cost_usd?: string;
  notes: string[];
}

interface MultiDesignResponse {
  reasoning_steps: ReasoningStep[];
  designs: DesignVariant[];
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: MultiDesignResponse;
}

/* ── Tab config ─────────────────────────────────────────────────────────── */

const VARIANT_CONFIG: Record<
  string,
  { icon: typeof DollarSign; color: string; accent: string; bg: string; ring: string; glow: string }
> = {
  "Cost Optimized": {
    icon: DollarSign,
    color: "text-[#EAC97C]",
    accent: "#EAC97C",
    bg: "bg-[#826015]/15",
    ring: "ring-[#826015]/40",
    glow: "shadow-[0_0_20px_rgba(130,96,21,0.15)]",
  },
  "Performance Optimized": {
    icon: Gauge,
    color: "text-[#0E7490]",
    accent: "#0E7490",
    bg: "bg-[#0E7490]/10",
    ring: "ring-[#0E7490]/40",
    glow: "shadow-[0_0_20px_rgba(14,116,144,0.15)]",
  },
  "Space Optimized": {
    icon: Box,
    color: "text-[#059669]",
    accent: "#059669",
    bg: "bg-[#059669]/10",
    ring: "ring-[#059669]/40",
    glow: "shadow-[0_0_20px_rgba(5,150,105,0.15)]",
  },
};

/* ── Demo prompts ───────────────────────────────────────────────────────── */

const DEMO_PROMPTS = [
  {
    icon: Battery,
    label: "48V Electric Scooter Pack",
    prompt:
      "Design a 48V battery pack and BMS for a high-speed electric scooter with 130 km range, 8.5 kW peak motor power, ~4.0 kWh capacity, under 20 kg total weight, and passive cooling.",
  },
  {
    icon: Zap,
    label: "72V E-Rickshaw Battery",
    prompt:
      "Design a 72V battery pack and BMS for an electric rickshaw with 100 km range, 3 kW continuous motor, ~5.5 kWh capacity, under 35 kg, and air-cooled thermal management.",
  },
  {
    icon: Cpu,
    label: "48V E-Bike Power Pack",
    prompt:
      "Design a compact 48V battery pack and BMS for a premium electric bicycle with 80 km range, 750W mid-drive motor, ~1.5 kWh capacity, under 6 kg, using cylindrical cells with passive cooling.",
  },
];

/* ── Reasoning Steps Display ────────────────────────────────────────────── */

function ReasoningSteps({ steps }: { steps: ReasoningStep[] }) {
  return (
    <div className="mb-6 rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/10 p-5">
      <div className="mb-4 flex items-center gap-2">
        <BrainCircuit className="h-4 w-4 text-[#0E7490]" />
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#0E7490]">
          AI Analysis
        </h3>
      </div>
      <div className="space-y-0">
        {steps.map((step, i) => (
          <motion.div
            key={step.step_number}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35, delay: i * 0.3, ease: "easeOut" }}
            className="relative flex gap-3 pb-4 last:pb-0"
          >
            {/* Vertical connector line */}
            {i < steps.length - 1 && (
              <motion.div
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ duration: 0.3, delay: i * 0.3 + 0.2 }}
                className="absolute left-[11px] top-[24px] h-[calc(100%-12px)] w-px origin-top bg-[#514733]"
              />
            )}
            {/* Step indicator */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.2, delay: i * 0.3 + 0.1 }}
              className="relative z-10 mt-0.5 flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-[#0E7490]/20 ring-1 ring-[#0E7490]/40"
            >
              <CheckCircle2 className="h-3 w-3 text-[#0E7490]" />
            </motion.div>
            {/* Content */}
            <div className="min-w-0 pt-0.5">
              <span className="text-sm font-medium text-[#EAC97C]">
                {step.title}
              </span>
              <p className="mt-0.5 text-xs leading-relaxed text-[#8F7E5E]">
                {step.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/* ── Design Variant Tabs + Content ──────────────────────────────────────── */

function DesignTabs({ designs }: { designs: DesignVariant[] }) {
  const [activeTab, setActiveTab] = useState(0);

  const totalSteps = designs.length > 0 ? 6 : 0; // assume ~6 reasoning steps max for delay calc
  const tabsDelay = totalSteps * 0.3 + 0.2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: tabsDelay }}
    >
      {/* Tab bar */}
      <div className="mb-4 flex gap-2 overflow-x-auto">
        {designs.map((d, i) => {
          const cfg = VARIANT_CONFIG[d.variant_name] || VARIANT_CONFIG["Cost Optimized"];
          const Icon = cfg.icon;
          const isActive = i === activeTab;

          return (
            <button
              key={d.variant_name}
              onClick={() => setActiveTab(i)}
              className={`group flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200 ring-1 ${
                isActive
                  ? `${cfg.bg} ${cfg.ring} ${cfg.color} ${cfg.glow}`
                  : "bg-transparent ring-[#514733]/40 text-[#8F7E5E] hover:ring-[#8F7E5E]/40 hover:text-[#B7AA91]"
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? cfg.color : "text-[#8F7E5E] group-hover:text-[#B7AA91]"}`} />
              {d.variant_name}
            </button>
          );
        })}
      </div>

      {/* Active variant content */}
      <AnimatePresence mode="wait">
        {designs[activeTab] && (
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <VariantContent design={designs[activeTab]} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ── Single Variant Content ─────────────────────────────────────────────── */

function VariantContent({ design }: { design: DesignVariant }) {
  const cfg = VARIANT_CONFIG[design.variant_name] || VARIANT_CONFIG["Cost Optimized"];

  return (
    <div className="space-y-4">
      {/* Variant header */}
      <div
        className="rounded-xl p-4"
        style={{
          background: `linear-gradient(135deg, ${cfg.accent}08 0%, ${cfg.accent}03 100%)`,
          border: `1px solid ${cfg.accent}20`,
        }}
      >
        <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: cfg.accent }}>
          {design.variant_name}
        </p>
        <p className="mt-1 text-sm text-[#B7AA91]">{design.variant_description}</p>
        {design.total_estimated_cost_usd && (
          <p className="mt-2 text-xs text-[#8F7E5E]">
            Estimated Total Cost:{" "}
            <span className="font-semibold text-[#EAC97C]">{design.total_estimated_cost_usd}</span>
          </p>
        )}
      </div>

      {/* Summary */}
      <div className="rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/20 p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EAC97C] mb-2">
          Project Summary
        </h3>
        <p className="text-sm leading-relaxed text-[#C8BAA6]">
          {design.project_summary}
        </p>
      </div>

      {/* Cell & Pack */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SpecCard title="Cell Specification" data={design.cell} />
        <SpecCard title="Pack Configuration" data={design.pack_configuration} />
      </div>

      {/* BMS & Cooling */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SpecCard title="BMS Specification" data={design.bms} />
        <SpecCard title="Thermal Management" data={design.cooling} />
      </div>

      {/* Design Choices */}
      <div className="rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/20 p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EAC97C] mb-3">
          Design Choices
        </h3>
        <div className="space-y-3">
          {design.design_choices.map((dc, i) => (
            <div key={i} className="border-l-2 pl-4" style={{ borderColor: cfg.accent }}>
              <div className="text-sm font-semibold text-[#EAC97C]">{dc.topic}</div>
              <div className="text-sm text-[#C8BAA6]">{dc.decision}</div>
              <div className="text-xs text-[#8F7E5E] mt-1 italic">{dc.rationale}</div>
            </div>
          ))}
        </div>
      </div>

      {/* BOM Table */}
      <div className="rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/20 p-5 overflow-x-auto">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EAC97C] mb-3">
          Bill of Materials
        </h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#8F7E5E]/30 text-[#EAC97C]">
              <th className="py-2 px-3 text-left">#</th>
              <th className="py-2 px-3 text-left">Component</th>
              <th className="py-2 px-3 text-left">Description</th>
              <th className="py-2 px-3 text-left">Qty</th>
              <th className="py-2 px-3 text-left">Specs</th>
              <th className="py-2 px-3 text-left">Est. Cost</th>
            </tr>
          </thead>
          <tbody>
            {design.bom_table.map((row, i) => (
              <tr
                key={i}
                className="border-b border-[#514733]/40 text-[#C8BAA6] hover:bg-[#514733]/20 transition-colors"
              >
                <td className="py-2 px-3">{row.item_number}</td>
                <td className="py-2 px-3 font-medium text-[#B7AA91]">{row.component_name}</td>
                <td className="py-2 px-3 text-xs">{row.description}</td>
                <td className="py-2 px-3">{row.quantity}</td>
                <td className="py-2 px-3 text-xs">{row.specifications}</td>
                <td className="py-2 px-3">{row.estimated_unit_cost_usd || "\u2014"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Notes */}
      {design.notes.length > 0 && (
        <div className="rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/20 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EAC97C] mb-2">
            Engineering Notes
          </h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-[#B7AA91]">
            {design.notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ── Spec Card ──────────────────────────────────────────────────────────── */

function SpecCard({
  title,
  data,
}: {
  title: string;
  data: Record<string, string | number | string[]>;
}) {
  return (
    <div className="rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/20 p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EAC97C] mb-3">
        {title}
      </h3>
      <dl className="space-y-2">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex justify-between gap-4">
            <dt className="text-xs text-[#8F7E5E] capitalize shrink-0">
              {key.replace(/_/g, " ")}
            </dt>
            <dd className="text-xs text-[#C8BAA6] text-right">
              {Array.isArray(value) ? value.join(", ") : String(value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/* ── Assistant Message (Reasoning + Designs) ────────────────────────────── */

function AssistantResponse({ data }: { data: MultiDesignResponse }) {
  return (
    <div className="w-full">
      <ReasoningSteps steps={data.reasoning_steps} />
      <DesignTabs designs={data.designs} />
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DemoPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Cycle loading phases for better UX
  useEffect(() => {
    if (!loading) {
      setLoadingPhase(0);
      return;
    }
    const timers = [
      setTimeout(() => setLoadingPhase(1), 3000),
      setTimeout(() => setLoadingPhase(2), 8000),
      setTimeout(() => setLoadingPhase(3), 15000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [loading]);

  const LOADING_MESSAGES = [
    "Analyzing your requirements...",
    "Selecting optimal components...",
    "Generating 3 design variants...",
    "Finalizing designs & BOM tables...",
  ];

  const sendQuery = async (query: string) => {
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: query,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/generate-bom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data: MultiDesignResponse = await res.json();

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        data,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Something went wrong. Make sure the backend is running on " + API_URL}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuery(input);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-screen flex-col bg-[#1E1B1B]">
      {/* Header */}
      <header className="shrink-0 border-b border-[#514733]/40 bg-[#1E1B1B]/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-6 py-4">
          <Link
            href="/"
            className="flex items-center gap-1 text-sm text-[#8F7E5E] transition-colors hover:text-[#EAC97C]"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Link>
          <div className="h-5 w-px bg-[#514733]" />
          <h1 className="font-[family-name:var(--font-space-grotesk)] text-lg font-bold text-[#EAC97C]">
            AEDI
          </h1>
          <span className="rounded-full bg-[#826015]/20 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[#826015] ring-1 ring-[#826015]/30">
            Demo
          </span>
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          {isEmpty ? (
            /* Empty state with demo prompts */
            <div className="flex h-full min-h-[60vh] flex-col items-center justify-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center"
              >
                <div className="mb-3 inline-flex items-center justify-center rounded-full bg-[#826015]/15 p-4 ring-1 ring-[#826015]/30">
                  <Zap className="h-8 w-8 text-[#EAC97C]" />
                </div>
                <h2 className="font-[family-name:var(--font-space-grotesk)] text-2xl font-bold text-[#EAC97C] sm:text-3xl">
                  Automated Electronic Design Initiative
                </h2>
                <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-[#8F7E5E]">
                  Describe your requirements and AEDI will analyze them, then
                  generate 3 optimized battery pack designs — Cost, Performance,
                  and Space optimized — each with a full Bill of Materials.
                </p>
              </motion.div>

              {/* Demo prompt cards */}
              <div className="mt-10 grid w-full max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
                {DEMO_PROMPTS.map((dp, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                    onClick={() => sendQuery(dp.prompt)}
                    className="group flex flex-col items-start gap-3 rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/15 p-5 text-left transition-all duration-200 hover:border-[#826015]/40 hover:bg-[#514733]/30 hover:shadow-[0_0_20px_rgba(130,96,21,0.1)]"
                  >
                    <dp.icon className="h-5 w-5 text-[#826015] transition-colors group-hover:text-[#EAC97C]" />
                    <span className="text-sm font-semibold text-[#EAC97C]">
                      {dp.label}
                    </span>
                    <span className="line-clamp-2 text-xs leading-relaxed text-[#8F7E5E]">
                      {dp.prompt}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            /* Chat messages */
            <div className="space-y-6">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`rounded-2xl px-5 py-4 ${
                        msg.role === "user"
                          ? "max-w-[85%] bg-[#826015]/30 border border-[#826015]/40 text-[#EAC97C]"
                          : "w-full bg-[#514733]/10 border border-[#8F7E5E]/10 text-[#C8BAA6]"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      ) : msg.data ? (
                        <AssistantResponse data={msg.data} />
                      ) : (
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center gap-3 rounded-2xl border border-[#8F7E5E]/15 bg-[#514733]/20 px-5 py-4">
                    <Loader2 className="h-4 w-4 animate-spin text-[#0E7490]" />
                    <span className="text-sm text-[#8F7E5E]">
                      {LOADING_MESSAGES[loadingPhase]}
                    </span>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="shrink-0 border-t border-[#514733]/40 bg-[#1E1B1B]/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-end gap-3 px-6 py-4">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your battery pack requirements..."
            rows={1}
            className="flex-1 resize-none rounded-xl border border-[#8F7E5E]/20 bg-[#514733]/15 px-4 py-3 text-sm text-[#EAC97C] placeholder-[#8F7E5E]/50 outline-none transition-colors focus:border-[#826015]/50 focus:ring-1 focus:ring-[#826015]/30"
            style={{ maxHeight: 120 }}
            onInput={(e) => {
              const el = e.target as HTMLTextAreaElement;
              el.style.height = "auto";
              el.style.height = Math.min(el.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={() => sendQuery(input)}
            disabled={!input.trim() || loading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#826015] text-[#1E1B1B] transition-all duration-200 hover:bg-[#8F7E5E] disabled:cursor-not-allowed disabled:opacity-30"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
