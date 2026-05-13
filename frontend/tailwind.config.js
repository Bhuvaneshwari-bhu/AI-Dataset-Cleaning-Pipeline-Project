/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0F0F12',
        card: {
          DEFAULT: '#1A1A22',
          elevated: '#24242E',
          hover: '#1F1F2A',
        },
        maroon: {
          300: '#E08FAF',
          400: '#CB6088',
          500: '#A63A50',
          600: '#7B1E3A',
          700: '#5C1629',
          800: '#3D0E1B',
        },
        ink: {
          DEFAULT: '#F5F5F5',
          secondary: '#B8B8C0',
          muted: '#6B6B78',
          accent: '#E8A0B0',
        },
        success: '#2E8B57',
        warning: '#D4A017',
        danger: '#C0392B',
      },
      boxShadow: {
        card: '0 4px 24px rgba(0,0,0,0.5)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.65)',
        'glow-maroon': '0 0 24px rgba(123,30,58,0.40)',
        'glow-maroon-sm': '0 0 14px rgba(123,30,58,0.25)',
        'glow-success': '0 0 14px rgba(46,139,87,0.25)',
      },
      backgroundImage: {
        'maroon-gradient': 'linear-gradient(135deg,#7B1E3A 0%,#A63A50 100%)',
        'maroon-gradient-r': 'linear-gradient(90deg,#7B1E3A 0%,#A63A50 100%)',
        'maroon-subtle': 'linear-gradient(135deg,rgba(123,30,58,0.12) 0%,rgba(166,58,80,0.08) 100%)',
        'hero-glow': 'radial-gradient(ellipse 80% 50% at 50% -10%,rgba(123,30,58,0.25) 0%,transparent 60%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.35s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'scale-in': 'scaleIn 0.25s ease-out',
        'glow-pulse': 'glowPulse 2.5s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'spin-slow': 'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        glowPulse: {
          '0%,100%': { boxShadow: '0 0 6px rgba(123,30,58,0.2)' },
          '50%': { boxShadow: '0 0 22px rgba(123,30,58,0.55)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
};
