'use client';

import { useState, useEffect } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { fetchDailyStats, fetchWeeklyStats, fetchMonthlyStats, StatItem } from '@/app/lib/api';
import { formatTime, getRankEmoji, getRankClass } from '@/app/lib/utils';

type Period = 'daily' | 'weekly' | 'monthly';

export default function StatsSection() {
  const t = useTranslations('stats');
  const locale = useLocale() as 'fa' | 'en';
  const [activePeriod, setActivePeriod] = useState<Period>('daily');
  const [stats, setStats] = useState<StatItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadStats = async (period: Period) => {
    setLoading(true);
    try {
      let data: StatItem[];
      switch (period) {
        case 'daily':
          data = await fetchDailyStats();
          break;
        case 'weekly':
          data = await fetchWeeklyStats();
          break;
        case 'monthly':
          data = await fetchMonthlyStats();
          break;
      }
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
      setStats([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadStats(activePeriod);
  }, [activePeriod]);

  const getTitle = () => {
    switch (activePeriod) {
      case 'daily':
        return t('todayTitle');
      case 'weekly':
        return t('weeklyTitle');
      case 'monthly':
        return t('monthlyTitle');
    }
  };

  const maxTime = stats.length > 0 ? Math.max(...stats.map(s => s.total_seconds)) : 0;

  return (
    <section className="rounded-2xl bg-card p-8 shadow-2xl border border-border/50">
      <div className="mb-8 flex flex-wrap items-center gap-3">
        {(['daily', 'weekly', 'monthly'] as Period[]).map((period) => (
          <button
            key={period}
            onClick={() => setActivePeriod(period)}
            className={`group relative overflow-hidden rounded-xl px-8 py-3 font-bold transition-all ${
              activePeriod === period
                ? 'bg-gradient-to-r from-primary to-accent text-white shadow-lg scale-105'
                : 'border-2 border-border bg-secondary/30 text-muted-foreground hover:border-primary/50 hover:scale-105'
            }`}
          >
            <span className="relative z-10">{t(period)}</span>
            {activePeriod !== period && (
              <div className="absolute inset-0 -z-0 bg-gradient-to-r from-primary/10 to-accent/10 opacity-0 transition-opacity group-hover:opacity-100" />
            )}
          </button>
        ))}
      </div>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {getTitle()}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {stats.length} {stats.length === 1 ? 'participant' : 'participants'}
          </p>
        </div>
        <button
          onClick={() => loadStats(activePeriod)}
          disabled={loading}
          className="group rounded-xl border-2 border-primary/30 bg-secondary/50 px-5 py-2.5 font-semibold transition-all hover:scale-105 hover:border-primary hover:shadow-lg disabled:opacity-50"
          title="Refresh"
        >
          <span className={`text-lg ${loading ? 'animate-spin inline-block' : ''}`}>
            {loading ? '⟳' : '🔄'}
          </span>
        </button>
      </div>

      {loading && stats.length === 0 ? (
        <div className="py-20 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      ) : stats.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground">
          <div className="mb-6 text-6xl animate-float">📊</div>
          <p className="text-lg font-semibold">{t('noStats')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {stats.map((item, index) => {
            const rank = index + 1;
            const rankClass = getRankClass(rank);
            const fieldDisplay = item.user.field_display?.[locale] || item.user.field || '';
            const gradeDisplay = item.user.grade_display?.[locale] || item.user.grade || '';
            const percentage = maxTime > 0 ? (item.total_seconds / maxTime) * 100 : 0;

            return (
              <div
                key={item.user.user_id}
                className={`group relative overflow-hidden rounded-2xl border-2 p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl ${rankClass}`}
                style={{
                  animationDelay: `${index * 50}ms`,
                  animation: 'slideUp 0.5s ease-out forwards',
                  opacity: 0
                }}
              >
                <div className="relative z-10 flex items-center justify-between mb-3">
                  <div className="flex items-center gap-5">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 text-3xl font-bold shadow-lg">
                      {getRankEmoji(rank)}
                    </div>
                    <div>
                      <h4 className="text-xl font-bold">{item.user.name || 'Unknown'}</h4>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <span className="px-2 py-0.5 bg-primary/10 rounded-md">{fieldDisplay}</span>
                        {gradeDisplay && (
                          <>
                            <span>•</span>
                            <span className="px-2 py-0.5 bg-accent/10 rounded-md">{gradeDisplay}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                      {formatTime(item.total_seconds, locale)}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Rank #{rank}
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="relative h-2 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-accent shadow-lg transition-all duration-1000 ease-out"
                    style={{
                      width: `${percentage}%`,
                      animationDelay: `${index * 100 + 300}ms`
                    }}
                  />
                </div>
              </div>
            );
          })}
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
