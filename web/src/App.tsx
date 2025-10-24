import { Navigate, Route, Routes } from 'react-router-dom';
import { UserProvider } from '@/context/UserContext';
import Home from '@/pages/Home';
import Upgrade from '@/pages/Upgrade';

export default function App() {
  return (
    <UserProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upgrade" element={<Upgrade />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </UserProvider>
  );
}
