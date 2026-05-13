import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

export default function MainLayout() {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-base">
      <Navbar />
      {/* key forces re-mount animation on route change */}
      <main key={pathname} className="flex-1 animate-fade-in">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
