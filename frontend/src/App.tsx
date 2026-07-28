import { useEffect, useState } from "react";
import { generateStream, getCurrentUser, getHistory, getHistoryItem, getToken, removeToken } from "./api";
import GenerateForm from "./components/GenerateForm";
import HistoryList from "./components/HistoryList";
import KnowledgeManager from "./components/KnowledgeManager";
import LoginForm from "./components/LoginForm";
import ResultsView from "./components/ResultsView";
import type { GenerateRequest, GenerateResponse, HistoryItem, UserOut, VariantOut } from "./types";

type Tab = "generate" | "knowledge";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserOut | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("generate");
  const [currentResult, setCurrentResult] = useState<GenerateResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    const token = getToken();
    if (!token) {
      setIsCheckingAuth(false);
      return;
    }

    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
      setIsAuthenticated(true);
      refreshHistory();
    } catch {
      removeToken();
      setIsAuthenticated(false);
    } finally {
      setIsCheckingAuth(false);
    }
  }

  function handleLoginSuccess() {
    checkAuth();
  }

  function handleLogout() {
    removeToken();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentResult(null);
    setHistory([]);
  }

  async function refreshHistory() {
    try {
      const items = await getHistory();
      setHistory(items);
    } catch {
      // history fetch failure is non-fatal for MVP; leave list empty
    }
  }

  async function handleGenerate(req: GenerateRequest) {
    setIsLoading(true);
    setError(null);
    setCurrentResult(null); // 清空之前的结果

    try {
      // 使用流式API
      const partialVariants: VariantOut[] = [];
      let requestId: number | null = null;
      let topic = "";
      let brandTone = "";
      let createdAt = "";

      await generateStream(
        req,
        // onVariant: 每收到一个变体就更新UI
        (variant) => {
          partialVariants.push(variant);
          // 实时更新显示
          if (requestId !== null) {
            setCurrentResult({
              request_id: requestId,
              topic,
              brand_tone: brandTone,
              created_at: createdAt,
              variants: [...partialVariants],
            });
          }
        },
        // onComplete: 所有变体完成
        (data) => {
          requestId = data.request_id;
          topic = data.topic;
          brandTone = data.brand_tone;
          createdAt = data.created_at;
          setCurrentResult({
            request_id: data.request_id,
            topic: data.topic,
            brand_tone: data.brand_tone,
            created_at: data.created_at,
            variants: partialVariants,
          });
          refreshHistory();
        },
        // onError: 错误处理
        (errorMsg) => {
          setError(errorMsg);
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSelectHistoryItem(requestId: number) {
    setError(null);
    try {
      const result = await getHistoryItem(requestId);
      setCurrentResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载历史记录失败");
    }
  }

  function handleRated(variantId: number, score: number, isFavorite: boolean) {
    setCurrentResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        variants: prev.variants.map((v) =>
          v.id === variantId ? { ...v, rating: { score, is_favorite: isFavorite } } : v,
        ),
      };
    });
  }

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">加载中...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="flex min-h-screen flex-col">
        <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-900 shadow-lg">
          <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-3 px-4 py-4 sm:px-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/20 text-lg">
                  ✦
                </div>
                <div>
                  <h1 className="text-lg font-bold leading-tight text-white">AI 社交文案生成助手</h1>
                  <p className="text-xs text-slate-400">LinkedIn · Facebook 高质量推文生成</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="hidden text-sm text-slate-300 sm:block">
                  {currentUser?.full_name || currentUser?.username}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm font-medium text-slate-300 hover:border-slate-500 hover:bg-slate-700/50 hover:text-white transition-colors"
                >
                  退出
                </button>
              </div>
            </div>
            <nav className="flex gap-1">
              <button
                type="button"
                onClick={() => setActiveTab("generate")}
                className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                  activeTab === "generate"
                    ? "bg-blue-500 text-white shadow-sm"
                    : "text-slate-400 hover:bg-slate-700/50 hover:text-white"
                }`}
              >
                生成文案
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("knowledge")}
                className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                  activeTab === "knowledge"
                    ? "bg-blue-500 text-white shadow-sm"
                    : "text-slate-400 hover:bg-slate-700/50 hover:text-white"
                }`}
              >
                企业知识库
              </button>
            </nav>
          </div>
        </header>

        {activeTab === "generate" ? (
          <main className="mx-auto grid w-full max-w-[1600px] flex-1 gap-6 px-4 py-6 sm:px-6 xl:grid-cols-[minmax(340px,420px)_minmax(0,1fr)] 2xl:grid-cols-[minmax(360px,440px)_minmax(0,1fr)]">
            <div className="flex min-h-0 flex-col gap-6 xl:max-h-[calc(100vh-8.5rem)] xl:sticky xl:top-6">
              <GenerateForm isLoading={isLoading} onSubmit={handleGenerate} />
              <HistoryList items={history} onSelect={handleSelectHistoryItem} />
            </div>

            <div className="min-w-0">
              <ResultsView
                result={currentResult}
                isLoading={isLoading}
                error={error}
                onRated={handleRated}
              />
            </div>
          </main>
        ) : (
          <KnowledgeManager />
        )}
      </div>
    </div>
  );
}
