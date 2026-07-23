import { useEffect, useState } from "react";
import { generate, getCurrentUser, getHistory, getHistoryItem, getToken, removeToken } from "./api";
import GenerateForm from "./components/GenerateForm";
import HistoryList from "./components/HistoryList";
import KnowledgeManager from "./components/KnowledgeManager";
import LoginForm from "./components/LoginForm";
import ResultsView from "./components/ResultsView";
import type { GenerateRequest, GenerateResponse, HistoryItem, UserOut } from "./types";

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
    try {
      const result = await generate(req);
      setCurrentResult(result);
      await refreshHistory();
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
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 px-4 py-4 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-slate-800">AI 社交文案生成助手</h1>
                <p className="text-sm text-slate-500">面向 LinkedIn / Facebook 的高质量推文生成</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-600">
                  欢迎，{currentUser?.full_name || currentUser?.username}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  退出登录
                </button>
              </div>
            </div>
            <nav className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setActiveTab("generate")}
                className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                  activeTab === "generate"
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                生成文案
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("knowledge")}
                className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                  activeTab === "knowledge"
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                企业知识库管理
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
