"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { startPipeline, ApiError } from "@/lib/api";
import type { WorkItemSource } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [workItemId, setWorkItemId] = useState("");
  const [source, setSource] = useState<WorkItemSource>("linear");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    if (!workItemId.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await startPipeline(workItemId.trim(), source);
      router.push(`/run/${res.run_id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === "NETWORK_ERROR") {
          // Backend not running — use mock mode
          router.push(`/run/demo-${Date.now()}?mock=true`);
          return;
        }
        setError(err.message);
      } else {
        setError("Something went wrong");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = () => {
    router.push(`/run/demo-${Date.now()}?mock=true`);
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brand}>
            <div className={styles.logo}>
              <span className={styles.logoIcon}>⚡</span>
              <span className={styles.logoText}>AutoPR</span>
            </div>
            <Badge variant="info" size="md">v0.1.0</Badge>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className={styles.main}>
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Work Item → Pull Request
            <span className={styles.heroAccent}> in seconds</span>
          </h1>
          <p className={styles.heroSubtitle}>
            AutoPR reads your ticket, understands the codebase, writes the code,
            validates it, and opens a PR — all autonomously.
          </p>
        </section>

        {/* Start Pipeline Form */}
        <Card variant="elevated" padding="lg">
          <h2 className={styles.formTitle}>Start a Pipeline Run</h2>

          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label htmlFor="work-item-id" className={styles.label}>
                Work Item ID
              </label>
              <input
                id="work-item-id"
                type="text"
                placeholder="e.g. AUT-42"
                value={workItemId}
                onChange={(e) => setWorkItemId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStart()}
                className={styles.input}
              />
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="source-select" className={styles.label}>
                Source
              </label>
              <select
                id="source-select"
                value={source}
                onChange={(e) => setSource(e.target.value as WorkItemSource)}
                className={styles.select}
              >
                <option value="linear">Linear</option>
                <option value="github">GitHub Issues</option>
              </select>
            </div>

            <div className={styles.actions}>
              <Button
                size="lg"
                onClick={handleStart}
                loading={loading}
                disabled={!workItemId.trim()}
              >
                🚀 Start Pipeline
              </Button>
            </div>
          </div>

          {error && <p className={styles.error}>{error}</p>}
        </Card>

        {/* Demo Section */}
        <Card variant="outlined" padding="md">
          <div className={styles.demoSection}>
            <div>
              <h3 className={styles.demoTitle}>🎬 Demo Mode</h3>
              <p className={styles.demoDesc}>
                Run a simulated pipeline with mock events — no backend required.
                See the full workflow visualization in action.
              </p>
            </div>
            <Button variant="secondary" size="lg" onClick={handleDemo}>
              ▶ Launch Demo
            </Button>
          </div>
        </Card>

        {/* Innovation Features */}
        <section className={styles.features}>
          <h2 className={styles.featuresTitle}>Innovation Features</h2>
          <div className={styles.featureGrid}>
            {[
              { icon: "🎬", title: "Live Workflow Visualization", desc: "Animated pipeline graph with real-time tool calls" },
              { icon: "🧠", title: "Confidence Scoring & HITL", desc: "Agent self-rates confidence; low scores trigger approval" },
              { icon: "🔄", title: "Failure Demo Mode", desc: "Inject a bug and watch the agent diagnose & fix it" },
              { icon: "📝", title: "BRD Injection", desc: "Drop a new BRD doc; agent adapts implementation live" },
              { icon: "🔍", title: "Code Diff Preview", desc: "Rich side-by-side diff before PR creation" },
              { icon: "💬", title: "NL PR Summary", desc: "Human-quality PR description explaining what/why/how" },
            ].map((f, i) => (
              <div key={i} className={styles.featureCard}>
                <span className={styles.featureIcon}>{f.icon}</span>
                <h3 className={styles.featureCardTitle}>{f.title}</h3>
                <p className={styles.featureCardDesc}>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
