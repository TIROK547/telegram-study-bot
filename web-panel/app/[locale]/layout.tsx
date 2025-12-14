import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { ThemeProvider } from 'next-themes';
import { ReactNode } from 'react';
import '../globals.css';

type Props = {
  children: ReactNode;
  params: { locale: string };
};

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;

  return {
    title: locale === 'fa' ? 'پنل آمار مطالعه' : 'Study Stats Panel',
    description: locale === 'fa' ? 'آمار و رتبه‌بندی زمان مطالعه' : 'Study time statistics and leaderboards',
  };
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;
  const messages = await getMessages();
  const dir = locale === 'fa' ? 'rtl' : 'ltr';

  return (
    <html lang={locale} dir={dir} suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          <NextIntlClientProvider messages={messages}>
            {children}
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
