
import React, { useState, useRef } from 'react';
import { 
  Sparkles, 
  Image as ImageIcon, 
  Upload, 
  Download, 
  History, 
  Trash2, 
  Loader2,
  Maximize2,
  AlertCircle,
  Menu,
  User
} from 'lucide-react';
import { AppMode, AspectRatio, GenerationHistoryItem } from './types';
import { generateImage, editImage } from './geminiService';

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>(AppMode.GENERATE);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentImage, setCurrentImage] = useState<string | null>(null);
  const [sourceImage, setSourceImage] = useState<{data: string, type: string} | null>(null);
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [history, setHistory] = useState<GenerationHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const data = event.target?.result as string;
        setSourceImage({ data, type: file.type });
        setCurrentImage(data);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      let resultUrl: string;
      if (mode === AppMode.GENERATE) {
        resultUrl = await generateImage(prompt, aspectRatio);
      } else {
        if (!sourceImage) {
          setError("Пожалуйста, загрузите изображение.");
          setLoading(false);
          return;
        }
        resultUrl = await editImage(sourceImage.data, sourceImage.type, prompt, aspectRatio);
      }

      setCurrentImage(resultUrl);
      
      const newHistoryItem: GenerationHistoryItem = {
        id: Math.random().toString(36).substr(2, 9),
        url: resultUrl,
        prompt: prompt,
        timestamp: Date.now(),
        mode: mode
      };
      setHistory(prev => [newHistoryItem, ...prev].slice(0, 20));
    } catch (err: any) {
      setError(err.message || "Произошла ошибка при генерации. Попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    if (!currentImage) return;
    const link = document.createElement('a');
    link.href = currentImage;
    link.download = `study-task-image-${Date.now()}.png`;
    link.click();
  };

  const clearHistory = () => setHistory([]);

  return (
    <div className="min-h-screen bg-[#F0F4FF] text-[#1e293b]">
      {/* Navigation Header */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50 px-4 md:px-8 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <span className="text-[#407BFF] font-black text-2xl tracking-tighter italic">STUDY TASK</span>
            </div>
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
              <a href="#" className="hover:text-[#407BFF]">Главная</a>
              <a href="#" className="hover:text-[#407BFF]">Как это работает</a>
              <a href="#" className="hover:text-[#407BFF]">Бесплатно</a>
              <a href="#" className="hover:text-[#407BFF]">Тарифы</a>
              <a href="#" className="hover:text-[#407BFF]">Контакты</a>
            </div>
          </div>
          <button className="flex items-center gap-2 px-6 py-2 rounded-full border border-[#407BFF] text-[#407BFF] font-semibold hover:bg-blue-50 transition-colors">
            <User className="w-4 h-4" />
            Войти
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
        {/* Intro Section */}
        <div className="text-center space-y-3 mb-8">
          <h2 className="text-4xl md:text-5xl font-black text-[#1e293b] leading-tight">
            Генератор иллюстраций <span className="text-[#407BFF]">для обучения</span>
          </h2>
          <p className="text-slate-500 max-w-2xl mx-auto">
            Создавайте уникальные изображения для своих квизов, презентаций и уроков с помощью искусственного интеллекта.
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Controls Card */}
          <div className="lg:col-span-4 space-y-6">
            <div className="st-card p-6 space-y-6">
              <div className="flex p-1 bg-slate-100 rounded-full">
                <button 
                  onClick={() => { setMode(AppMode.GENERATE); setCurrentImage(null); }}
                  className={`flex-1 py-2.5 rounded-full text-sm font-bold transition-all ${mode === AppMode.GENERATE ? 'bg-[#407BFF] text-white shadow-md' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  Создать
                </button>
                <button 
                  onClick={() => { setMode(AppMode.EDIT); setCurrentImage(null); }}
                  className={`flex-1 py-2.5 rounded-full text-sm font-bold transition-all ${mode === AppMode.EDIT ? 'bg-[#407BFF] text-white shadow-md' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  Изменить
                </button>
              </div>

              {mode === AppMode.EDIT && (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="group relative h-40 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-[#407BFF]/50 transition-all"
                >
                  <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileUpload} />
                  {sourceImage ? (
                    <img src={sourceImage.data} className="absolute inset-0 w-full h-full object-cover rounded-xl opacity-20" />
                  ) : null}
                  <Upload className="w-8 h-8 text-slate-400 group-hover:text-[#407BFF] transition-colors" />
                  <p className="text-sm font-medium text-slate-500">Загрузить фото</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Описание (Промпт)</label>
                  <textarea 
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={mode === AppMode.GENERATE ? "Например: Ученик за партой в стиле 3D иллюстрации..." : "Например: Добавь ученику очки и книгу..."}
                    className="w-full h-32 bg-slate-50 border border-slate-200 rounded-2xl p-4 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#407BFF]/20 focus:border-[#407BFF] resize-none transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Формат</label>
                  <div className="grid grid-cols-5 gap-2">
                    {(['1:1', '4:3', '3:4', '16:9', '9:16'] as AspectRatio[]).map((ratio) => (
                      <button
                        key={ratio}
                        type="button"
                        onClick={() => setAspectRatio(ratio)}
                        className={`py-2 text-xs rounded-lg border font-medium transition-all ${aspectRatio === ratio ? 'bg-[#407BFF] text-white border-[#407BFF]' : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'}`}
                      >
                        {ratio}
                      </button>
                    ))}
                  </div>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-100 rounded-xl p-3 flex items-center gap-2 text-red-600 text-xs">
                    <AlertCircle className="w-4 h-4" />
                    <p>{error}</p>
                  </div>
                )}

                <button 
                  type="submit"
                  disabled={loading || !prompt.trim() || (mode === AppMode.EDIT && !sourceImage)}
                  className="w-full st-button-primary font-bold py-4 rounded-2xl flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 disabled:bg-slate-300 disabled:shadow-none transition-all"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Создаю...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      {mode === AppMode.GENERATE ? 'Сгенерировать' : 'Обновить'}
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="lg:col-span-8 space-y-8">
            <div className="st-card overflow-hidden relative min-h-[400px] flex items-center justify-center bg-slate-50 border-slate-200/60">
              {loading && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm z-20 transition-all animate-in fade-in">
                  <div className="w-16 h-16 border-4 border-[#407BFF]/10 border-t-[#407BFF] rounded-full animate-spin mb-4" />
                  <p className="text-[#407BFF] font-bold animate-pulse-soft">Готовим вашу иллюстрацию...</p>
                </div>
              )}

              {currentImage ? (
                <div className="relative w-full h-full group">
                  <img src={currentImage} alt="Preview" className="w-full h-full object-contain max-h-[600px] mx-auto" />
                  <div className="absolute bottom-6 right-6 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={downloadImage} className="bg-white p-3 rounded-full shadow-lg text-[#407BFF] hover:bg-blue-50 transition-colors">
                      <Download className="w-6 h-6" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4 text-slate-300 py-20">
                  <ImageIcon className="w-24 h-24 stroke-1 opacity-20" />
                  <p className="font-medium text-slate-400">Изображение появится здесь</p>
                </div>
              )}
            </div>

            {/* History Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold flex items-center gap-2 text-slate-700">
                  <History className="w-5 h-5 text-[#407BFF]" />
                  Недавние работы
                </h3>
                <button onClick={clearHistory} className="text-slate-400 hover:text-red-500 text-sm flex items-center gap-1 transition-colors">
                  <Trash2 className="w-4 h-4" />
                  Очистить
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-4">
                {history.length > 0 ? history.map((item) => (
                  <div 
                    key={item.id} 
                    onClick={() => setCurrentImage(item.url)}
                    className="aspect-square st-card overflow-hidden cursor-pointer hover:ring-2 hover:ring-[#407BFF] transition-all group relative border-none"
                  >
                    <img src={item.url} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-[#407BFF]/20 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                      <Maximize2 className="w-6 h-6 text-white" />
                    </div>
                  </div>
                )) : (
                  Array.from({length: 5}).map((_, i) => (
                    <div key={i} className="aspect-square bg-slate-200/50 rounded-2xl border border-slate-100" />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-100 mt-20 py-12">
        <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-[#407BFF] font-black text-xl italic tracking-tighter">STUDY TASK</div>
          <p className="text-slate-400 text-sm">© 2024 Study Task — Образовательная платформа нового поколения</p>
          <div className="flex gap-4 text-slate-400">
            <a href="#" className="hover:text-[#407BFF]">Политика</a>
            <a href="#" className="hover:text-[#407BFF]">Помощь</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
