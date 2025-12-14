'use client';

import { useTheme } from 'next-themes';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Header() {
  const { theme, setTheme } = useTheme();
  const t = useTranslations('app');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleLanguage = () => {
    const newLocale = locale === 'fa' ? 'en' : 'fa';
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPath);
  };

  if (!mounted) {
    return null;
  }

  return (
    <header className="sticky top-0 z-50 w-full glass border-b shadow-lg">
      <div className="container mx-auto px-4 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-2xl shadow-lg animate-float">
              🎓
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                {t('title')}
              </h1>
              <p className="text-xs text-muted-foreground">{t('description')}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="group relative overflow-hidden rounded-xl border-2 border-primary/20 bg-secondary/50 px-5 py-2.5 text-sm font-semibold transition-all hover:scale-105 hover:border-primary/40 hover:shadow-lg"
              title={t('theme')}
            >
              <span className="relative z-10 flex items-center gap-2">
                {theme === 'dark' ? '☀️' : '🌙'}
                <span className="hidden sm:inline">{theme === 'dark' ? 'Light' : 'Dark'}</span>
              </span>
              <div className="absolute inset-0 -z-0 bg-gradient-to-r from-primary/10 to-accent/10 opacity-0 transition-opacity group-hover:opacity-100" />
            </button>

            <button
              onClick={toggleLanguage}
              className="group relative overflow-hidden rounded-xl border-2 border-accent/20 bg-secondary/50 px-5 py-2.5 text-sm font-semibold transition-all hover:scale-105 hover:border-accent/40 hover:shadow-lg"
            >
              <span className="relative z-10 flex items-center gap-2">
                🌐
                <span>{locale === 'fa' ? 'EN' : 'فا'}</span>
              </span>
              <div className="absolute inset-0 -z-0 bg-gradient-to-r from-accent/10 to-primary/10 opacity-0 transition-opacity group-hover:opacity-100" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
