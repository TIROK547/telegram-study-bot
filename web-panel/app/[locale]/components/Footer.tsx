import { useTranslations } from 'next-intl';

export default function Footer() {
  const t = useTranslations('footer');

  return (
    <footer className="mt-auto border-t border-border/50 bg-card/50 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-6">
          {/* Logo/Icon */}
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-3xl shadow-lg animate-float">
            🎓
          </div>

          {/* Made with love */}
          <div className="text-center">
            <p className="mb-4 flex items-center justify-center gap-2 text-muted-foreground">
              <span>{t('madeWith')}</span>
              <span className="animate-pulse text-xl text-red-500">❤️</span>
            </p>

            {/* Developer info */}
            <div className="flex items-center justify-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">
                {t('developer')}
              </span>
              <a
                href="https://t.me/tirok547"
                target="_blank"
                rel="noopener noreferrer"
                className="group relative inline-flex items-center gap-2 rounded-xl border-2 border-primary/30 bg-gradient-to-r from-primary/10 to-accent/10 px-5 py-2.5 font-bold transition-all hover:scale-105 hover:border-primary hover:shadow-lg"
              >
                <span className="text-xl">📱</span>
                <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  @tirok547
                </span>
              </a>
            </div>
          </div>

          {/* Copyright */}
          <div className="text-xs text-muted-foreground/70">
            © {new Date().getFullYear()} Study Stats Panel. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
