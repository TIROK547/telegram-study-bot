import Header from './components/Header';
import Footer from './components/Footer';
import SearchSection from './components/SearchSection';
import StatsSection from './components/StatsSection';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 py-12">
        <div className="container mx-auto space-y-12 px-4 max-w-7xl">
          {/* Hero Section */}
          <div className="text-center py-8">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-float">
              Track Your Study Progress
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Monitor your daily, weekly, and monthly study statistics. Stay motivated and see how you rank!
            </p>
          </div>

          <SearchSection />
          <StatsSection />
        </div>
      </main>

      <Footer />
    </div>
  );
}
