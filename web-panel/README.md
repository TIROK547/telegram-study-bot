# Study Bot - Next.js Web Panel

Modern, bilingual web panel for the Study Bot with dark/light theme support.

## Features

- ✅ **Next.js 15** with App Router
- ✅ **TypeScript** for type safety
- ✅ **Tailwind CSS** for styling
- ✅ **Dark/Light Theme** with next-themes
- ✅ **Internationalization** (Farsi/English) with next-intl
- ✅ **Responsive Design** for mobile and desktop
- ✅ **Server Components** for better performance
- ✅ **API Integration** with FastAPI backend

## Getting Started

### Installation

```bash
npm install
```

### Configuration

Create a `.env.local` file (copy from `.env.local.example`):

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Running Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

The app will default to Farsi (fa) locale. To access English version, go to [http://localhost:3000/en](http://localhost:3000/en).

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
web-panel/
├── app/
│   ├── [locale]/              # Locale-specific routes
│   │   ├── components/        # React components
│   │   │   ├── Header.tsx     # Header with theme/language toggle
│   │   │   ├── Footer.tsx     # Footer with creator info
│   │   │   ├── SearchSection.tsx   # User search
│   │   │   └── StatsSection.tsx    # Statistics tabs
│   │   ├── layout.tsx         # Locale layout
│   │   └── page.tsx           # Home page
│   ├── lib/
│   │   ├── api.ts             # API functions
│   │   └── utils.ts           # Utility functions
│   ├── globals.css            # Global styles
│   └── layout.tsx             # Root layout
├── messages/
│   ├── fa.json                # Farsi translations
│   └── en.json                # English translations
├── public/                    # Static files
├── i18n.ts                    # i18n configuration
├── middleware.ts              # Next.js middleware for i18n
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind configuration
└── tsconfig.json              # TypeScript configuration
```

## Features Breakdown

### Theme Toggle
- Light and dark themes using `next-themes`
- Persists theme preference in localStorage
- Smooth transitions between themes

### Language Support
- Farsi (RTL) and English (LTR) with `next-intl`
- URL-based locale switching
- Proper RTL/LTR direction handling
- All text content is translatable

### Search Functionality
- Search users by username (@username)
- Display user profile (field, grade)
- Show daily, weekly, monthly, and total study time

### Statistics
- Three tabs: Daily, Weekly, Monthly
- Real-time data from FastAPI backend
- Leaderboard with medal badges for top 3
- Automatic refresh functionality
- Empty states when no data

### Responsive Design
- Mobile-first approach
- Grid layouts that adapt to screen size
- Touch-friendly buttons and interactions
- Optimized for all devices

## API Integration

The app connects to the FastAPI backend running on `localhost:8000`.

API endpoints used:
- `/api/stats/daily` - Daily statistics
- `/api/stats/weekly` - Weekly statistics
- `/api/stats/monthly` - Monthly statistics
- `/api/user/{username}` - User search

## Customization

### Adding New Translations

Edit `messages/fa.json` and `messages/en.json`:

```json
{
  "newKey": "New Value"
}
```

Use in components:
```tsx
const t = useTranslations('newKey');
<p>{t('newKey')}</p>
```

### Styling

The project uses Tailwind CSS. Customize colors and styles in:
- `tailwind.config.ts` - Theme configuration
- `app/globals.css` - Global styles and CSS variables

### Adding New Pages

Create a new file in `app/[locale]/your-page/page.tsx`:

```tsx
export default function YourPage() {
  return <div>Your content</div>;
}
```

## Deployment

### Vercel (Recommended)

```bash
npm run build
vercel deploy
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Static Export

```bash
npm run build
# Outputs to .next/
```

## Dependencies

### Core
- `next` - React framework
- `react` & `react-dom` - React library
- `typescript` - Type safety

### UI & Styling
- `tailwindcss` - Utility-first CSS
- `next-themes` - Theme management
- `next-intl` - Internationalization

### Dev Dependencies
- `@types/*` - TypeScript definitions
- `eslint` - Code linting
- `autoprefixer` - CSS prefixing

## Troubleshooting

### API Connection Issues
- Ensure FastAPI backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS is enabled on the backend

### Build Errors
- Clear `.next` folder: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run build`

### Theme Not Working
- Ensure `ThemeProvider` is in the layout
- Check browser localStorage
- Clear cache and reload

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions, contact [@tirok547](https://t.me/tirok547)

## License

Educational purposes only.
