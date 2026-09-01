import { BenchmarkPanel } from "@/features/optimization/components/BenchmarkPanel";

// SSG(静的生成)のまま ── バックエンドへの問い合わせは BenchmarkPanel(client)側で行う。
export default function BenchmarkPage() {
  return <BenchmarkPanel />;
}
