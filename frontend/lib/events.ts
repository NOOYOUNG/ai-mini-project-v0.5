/**
 * 이벤트 스키마 (Backend app/events.py 와 같은 형식)
 * 한쪽을 바꾸면 다른 쪽도 함께 바꿔야 합니다.
 */
export type RunStart = { type: "run_start"; ts: number; run_id: string; item_id: string; item_name: string; competitors: string[]; query: string; test_mode: boolean };
export type NodeStart = { type: "node_start"; ts: number; node: string };
export type NodeEnd = { type: "node_end"; ts: number; node: string; duration_ms: number };
export type BranchStart = { type: "branch_start"; ts: number; node: string; branch: string };
export type BranchEnd = { type: "branch_end"; ts: number; node: string; branch: string; duration_ms: number };
export type Route = { type: "route"; ts: number; source: string; target: string; reason: string };
export type Progress = { type: "progress"; ts: number; node: string; message: string };
export type LlmUsage = { type: "llm_usage"; ts: number; node: string; model: string; input_tokens: number; output_tokens: number; cost_usd: number };
export type Evaluation = { type: "evaluation"; ts: number; stage: string; passed: boolean; reason: string; attempt: number };
export type Token = { type: "token"; ts: number; node: string; text: string };
export type Report = { type: "report"; ts: number; run_id: string; markdown: string };
export type ErrorEvent = { type: "error"; ts: number; message: string };
export type Done = { type: "done"; ts: number; run_id: string; total_duration_ms: number; llm_calls: number; input_tokens: number; output_tokens: number; total_cost_usd: number };

export type AgentEvent =
  | RunStart | NodeStart | NodeEnd | BranchStart | BranchEnd | Route | Progress
  | LlmUsage | Evaluation | Token | Report | ErrorEvent | Done;

export type ItemConfig = {
  name: string;
  competitors: string[];
  test_questions: Record<string, string>;
};
