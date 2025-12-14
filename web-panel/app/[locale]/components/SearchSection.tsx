'use client';

import { useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { searchUser, UserResponse } from '@/app/lib/api';
import { formatTime } from '@/app/lib/utils';

export default function SearchSection() {
  const t = useTranslations('search');
  const tStats = useTranslations('stats');
  const locale = useLocale() as 'fa' | 'en';
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UserResponse | null | undefined>(undefined);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    const data = await searchUser(query);
    setResult(data);
    setLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <section className="rounded-2xl bg-card p-8 shadow-2xl border border-border/50">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-2xl shadow-lg">
          🔍
        </div>
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {t('title')}
          </h2>
          <p className="text-xs text-muted-foreground">Search by username</p>
        </div>
      </div>

      <div className="mb-6 flex gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t('placeholder')}
            className="w-full rounded-xl border-2 border-border bg-secondary/30 px-5 py-4 pr-12 outline-none transition-all focus:border-primary focus:shadow-lg focus:scale-[1.02]"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground">
            👤
          </div>
        </div>
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="group relative overflow-hidden rounded-xl bg-gradient-to-r from-primary to-accent px-8 py-4 font-bold text-white shadow-lg transition-all hover:scale-105 hover:shadow-xl disabled:opacity-50 disabled:hover:scale-100"
        >
          <span className="relative z-10">
            {loading ? (
              <span className="inline-block animate-spin">⟳</span>
            ) : (
              t('button')
            )}
          </span>
        </button>
      </div>

      {result === null && (
        <div className="py-16 text-center text-muted-foreground">
          <div className="mb-6 text-6xl animate-float">🔍</div>
          <p className="text-lg font-semibold">{t('noResults')}</p>
          <p className="text-sm mt-2">Try searching with a different username</p>
        </div>
      )}

      {result && (
        <div
          className="rounded-2xl border-2 border-primary/20 bg-gradient-to-br from-secondary/50 to-secondary/30 p-8 shadow-xl transition-all duration-300 hover:scale-[1.01] hover:shadow-2xl"
          style={{
            animation: 'slideUp 0.5s ease-out'
          }}
        >
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-3xl shadow-lg">
              👤
            </div>
            <div>
              <h3 className="text-2xl font-bold">{result.user.name}</h3>
              <div className="flex items-center gap-2 mt-2">
                <span className="px-3 py-1 bg-primary/20 rounded-lg text-sm font-semibold text-primary">
                  {result.user.field_display[locale]}
                </span>
                <span className="px-3 py-1 bg-accent/20 rounded-lg text-sm font-semibold text-accent">
                  {result.user.grade_display[locale]}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: tStats('dailyTime'), value: result.stats.daily, icon: '📅', color: 'from-blue-500 to-blue-600' },
              { label: tStats('weeklyTime'), value: result.stats.weekly, icon: '📆', color: 'from-purple-500 to-purple-600' },
              { label: tStats('monthlyTime'), value: result.stats.monthly, icon: '🗓️', color: 'from-pink-500 to-pink-600' },
              { label: tStats('totalTime'), value: result.stats.total, icon: '⏱️', color: 'from-green-500 to-green-600' },
            ].map((stat, i) => (
              <div
                key={i}
                className="group relative overflow-hidden rounded-xl border-2 border-border bg-card p-4 text-center transition-all hover:scale-105 hover:shadow-lg"
                style={{
                  animation: `slideUp 0.5s ease-out ${i * 100 + 200}ms forwards`,
                  opacity: 0
                }}
              >
                <div className="mb-2 text-2xl">{stat.icon}</div>
                <div className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  {stat.label}
                </div>
                <div className={`text-xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`}>
                  {formatTime(stat.value, locale)}
                </div>
                <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-0 transition-opacity group-hover:opacity-10`} />
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </section>
  );
}
